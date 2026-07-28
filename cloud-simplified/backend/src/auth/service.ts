import { CognitoIdentityProviderClient, SignUpCommand, InitiateAuthCommand, GetUserCommand } from "@aws-sdk/client-cognito-identity-provider";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, PutCommand, GetCommand, QueryCommand, UpdateCommand } from "@aws-sdk/lib-dynamodb";
import { v4 as uuidv4 } from "uuid";
import jwt from "jsonwebtoken";

export interface User {
  id: string;
  email: string;
  name?: string;
  workspaceIds: string[];
  createdAt: string;
  lastLoginAt: string;
}

export interface Workspace {
  id: string;
  userId: string;
  name: string;
  s3Bucket: string;
  s3Prefix: string;
  status: "active" | "suspended" | "deleted";
  createdAt: string;
  updatedAt: string;
}

export class AuthService {
  private cognito: CognitoIdentityProviderClient;
  private dynamo: DynamoDBDocumentClient;
  private userPoolId: string;
  private clientId: string;
  private tableName: string;
  private jwtSecret: string;

  constructor() {
    const region = process.env.AWS_REGION || "us-east-1";
    const credentials = {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID || "",
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || "",
    };

    this.cognito = new CognitoIdentityProviderClient({ region, credentials });
    this.dynamo = DynamoDBDocumentClient.from(new DynamoDBClient({ region, credentials }));
    this.userPoolId = process.env.COGNITO_USER_POOL_ID || "";
    this.clientId = process.env.COGNITO_CLIENT_ID || "";
    this.tableName = process.env.USERS_TABLE || "rostr-users";
    this.jwtSecret = process.env.JWT_SECRET || "your-secret-key-change-in-production";
  }

  // Register new user
  async register(email: string, password: string, name?: string): Promise<{ userId: string; message: string }> {
    try {
      // Create user in Cognito
      const signUpResult = await this.cognito.send(new SignUpCommand({
        ClientId: this.clientId,
        Username: email,
        Password: password,
        UserAttributes: name ? [{ Name: "name", Value: name }] : [],
      }));

      const userId = signUpResult.UserSub || uuidv4();

      // Create user record in DynamoDB
      await this.dynamo.send(new PutCommand({
        TableName: this.tableName,
        Item: {
          pk: `USER#${userId}`,
          sk: `EMAIL#${email.toLowerCase()}`,
          id: userId,
          email: email.toLowerCase(),
          name: name || email.split("@")[0],
          workspaceIds: [],
          createdAt: new Date().toISOString(),
          lastLoginAt: new Date().toISOString(),
          ttl: Math.floor(Date.now() / 1000) + 365 * 24 * 60 * 60,
        },
      }));

      // Create default workspace
      await this.createDefaultWorkspace(userId, name || email.split("@")[0]);

      return {
        userId,
        message: "User registered successfully. Please check your email to confirm.",
      };
    } catch (error: any) {
      if (error.name === "UsernameExistsException") {
        throw new Error("User already exists");
      }
      throw error;
    }
  }

  // Login user
  async login(email: string, password: string): Promise<{ user: User; token: string; workspaceId: string }> {
    try {
      const authResult = await this.cognito.send(new InitiateAuthCommand({
        AuthFlow: "USER_PASSWORD_AUTH",
        ClientId: this.clientId,
        AuthParameters: {
          USERNAME: email.toLowerCase(),
          PASSWORD: password,
        },
      }));

      const accessToken = authResult.AuthenticationResult?.AccessToken;
      if (!accessToken) {
        throw new Error("Authentication failed");
      }

      // Get user info
      const userResult = await this.cognito.send(new GetUserCommand({
        AccessToken: accessToken,
      }));

      const userId = userResult.Username;
      const userEmail = userResult.UserAttributes?.find(a => a.Name === "email")?.Value || email;
      const userName = userResult.UserAttributes?.find(a => a.Name === "name")?.Value;

      // Get user from DynamoDB
      const user = await this.getUserFromDB(userId);

      // Update last login
      await this.updateLastLogin(userId);

      // Generate JWT
      const token = this.generateToken(userId, userEmail);

      // Get default workspace
      const workspaceId = user.workspaceIds[0] || await this.createDefaultWorkspace(userId, userName || userEmail.split("@")[0]);

      return {
        user,
        token,
        workspaceId,
      };
    } catch (error: any) {
      if (error.name === "NotAuthorizedException") {
        throw new Error("Invalid email or password");
      }
      throw error;
    }
  }

  // Get or create user from DB
  private async getUserFromDB(userId: string): Promise<User> {
    const result = await this.dynamo.send(new GetCommand({
      TableName: this.tableName,
      Key: {
        pk: `USER#${userId}`,
        sk: `EMAIL#`, // Prefix match
      },
    }));

    if (result.Item) {
      return {
        id: result.Item.id,
        email: result.Item.email,
        name: result.Item.name,
        workspaceIds: result.Item.workspaceIds || [],
        createdAt: result.Item.createdAt,
        lastLoginAt: result.Item.lastLoginAt,
      };
    }

    // User exists in Cognito but not in DB - create record
    throw new Error("User not found");
  }

  // Update last login
  private async updateLastLogin(userId: string): Promise<void> {
    await this.dynamo.send(new UpdateCommand({
      TableName: this.tableName,
      Key: {
        pk: `USER#${userId}`,
        sk: `EMAIL#`,
      },
      UpdateExpression: "set lastLoginAt = :time",
      ExpressionAttributeValues: {
        ":time": new Date().toISOString(),
      },
    }));
  }

  // Create default workspace for new user
  private async createDefaultWorkspace(userId: string, name: string): Promise<string> {
    const workspaceId = uuidv4();
    const timestamp = new Date().toISOString();
    const s3Prefix = `workspaces/${userId}/${workspaceId}/`;

    // Create workspace record
    await this.dynamo.send(new PutCommand({
      TableName: this.tableName,
      Item: {
        pk: `WORKSPACE#${workspaceId}`,
        sk: `USER#${userId}`,
        id: workspaceId,
        userId,
        name: `${name}'s Workspace`,
        s3Bucket: process.env.GSTACK_S3_BUCKET || "rostr-gstack-workspaces",
        s3Prefix,
        status: "active",
        createdAt: timestamp,
        updatedAt: timestamp,
      },
    }));

    // Update user's workspace list
    const userResult = await this.dynamo.send(new GetCommand({
      TableName: this.tableName,
      Key: {
        pk: `USER#${userId}`,
        sk: `EMAIL#`,
      },
    }));

    const currentWorkspaces = userResult.Item?.workspaceIds || [];
    
    await this.dynamo.send(new UpdateCommand({
      TableName: this.tableName,
      Key: {
        pk: `USER#${userId}`,
        sk: `EMAIL#`,
      },
      UpdateExpression: "set workspaceIds = :workspaces",
      ExpressionAttributeValues: {
        ":workspaces": [...currentWorkspaces, workspaceId],
      },
    }));

    return workspaceId;
  }

  // Generate JWT token
  private generateToken(userId: string, email: string): string {
    return jwt.sign(
      { sub: userId, email, iat: Date.now() },
      this.jwtSecret,
      { expiresIn: "7d" }
    );
  }

  // Verify JWT token
  async verifyToken(token: string): Promise<{ userId: string; email: string }> {
    try {
      const decoded = jwt.verify(token, this.jwtSecret) as any;
      return {
        userId: decoded.sub,
        email: decoded.email,
      };
    } catch (error) {
      throw new Error("Invalid token");
    }
  }

  // Get user workspaces
  async getUserWorkspaces(userId: string): Promise<Workspace[]> {
    const result = await this.dynamo.send(new QueryCommand({
      TableName: this.tableName,
      KeyConditionExpression: "pk = :pk",
      ExpressionAttributeValues: {
        ":pk": `WORKSPACE#`,
      },
      FilterExpression: "userId = :userId",
      ExpressionAttributeValues: {
        ":userId": userId,
      },
    }));

    return (result.Items || []).map(item => ({
      id: item.id,
      userId: item.userId,
      name: item.name,
      s3Bucket: item.s3Bucket,
      s3Prefix: item.s3Prefix,
      status: item.status,
      createdAt: item.createdAt,
      updatedAt: item.updatedAt,
    }));
  }

  // Launch workspace (mark as active and return launch URL)
  async launchWorkspace(workspaceId: string, userId: string): Promise<{ url: string; workspace: Workspace }> {
    // Verify workspace belongs to user
    const result = await this.dynamo.send(new GetCommand({
      TableName: this.tableName,
      Key: {
        pk: `WORKSPACE#${workspaceId}`,
        sk: `USER#${userId}`,
      },
    }));

    if (!result.Item) {
      throw new Error("Workspace not found");
    }

    const workspace: Workspace = {
      id: result.Item.id,
      userId: result.Item.userId,
      name: result.Item.name,
      s3Bucket: result.Item.s3Bucket,
      s3Prefix: result.Item.s3Prefix,
      status: result.Item.status,
      createdAt: result.Item.createdAt,
      updatedAt: result.Item.updatedAt,
    };

    // Update last accessed
    await this.dynamo.send(new UpdateCommand({
      TableName: this.tableName,
      Key: {
        pk: `WORKSPACE#${workspaceId}`,
        sk: `USER#${userId}`,
      },
      UpdateExpression: "set updatedAt = :time",
      ExpressionAttributeValues: {
        ":time": new Date().toISOString(),
      },
    }));

    // Return launch URL with workspace ID
    return {
      url: `/app/${workspaceId}`,
      workspace,
    };
  }
}
