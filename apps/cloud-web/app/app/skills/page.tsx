"use client";

import { useState, useEffect } from "react";

interface Skill {
  id: string;
  name: string;
  description: string;
  createdAt: string;
}

export default function SkillsPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSkills();
  }, []);

  const fetchSkills = async () => {
    try {
      const response = await fetch("/api/skills/list");
      if (response.ok) {
        const data = await response.json();
        setSkills(data.skills || []);
      }
    } catch (error) {
      console.error("Failed to fetch skills:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/skills/upload", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        await fetchSkills();
      } else {
        alert("Upload failed");
      }
    } catch (error) {
      console.error("Upload error:", error);
      alert("Upload error");
    } finally {
      setUploading(false);
      if (e.target) e.target.value = "";
    }
  };

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-2">Skills Marketplace</h1>
        <p className="text-slate-400 mb-8">
          Upload custom skills or browse installed tools
        </p>

        {/* Upload Section */}
        <div className="mb-12">
          <label className="block p-8 border-2 border-dashed border-slate-700 rounded-lg hover:border-cyan-500 transition cursor-pointer text-center group">
            <input
              type="file"
              accept=".skill,.js,.ts"
              onChange={handleUpload}
              disabled={uploading}
              className="hidden"
            />
            <div className="group-hover:text-cyan-400 transition">
              <div className="text-4xl mb-2">📤</div>
              <p className="font-semibold">
                {uploading ? "Uploading..." : "Drop skill file here or click to browse"}
              </p>
              <p className="text-sm text-slate-400 mt-1">
                Supported: .skill, .js, .ts files
              </p>
            </div>
          </label>
        </div>

        {/* Skills Grid */}
        <div>
          <h2 className="text-2xl font-bold mb-4">Installed Skills</h2>
          {loading ? (
            <div className="text-center py-8 text-slate-400">
              Loading skills...
            </div>
          ) : skills.length === 0 ? (
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-8 text-center text-slate-400">
              <p className="mb-2">No skills installed yet</p>
              <p className="text-sm">Upload your first skill to get started</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {skills.map((skill) => (
                <div
                  key={skill.id}
                  className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 hover:border-cyan-500 transition group"
                >
                  <h3 className="font-semibold text-lg mb-2 group-hover:text-cyan-400 transition">
                    {skill.name}
                  </h3>
                  <p className="text-slate-400 text-sm mb-4">
                    {skill.description}
                  </p>
                  <div className="flex justify-between items-center text-xs text-slate-500">
                    <span>
                      Added{" "}
                      {new Date(skill.createdAt).toLocaleDateString()}
                    </span>
                    <button className="px-3 py-1 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 rounded transition">
                      Use
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
