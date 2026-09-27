"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createVideoJob, listVideoJobs, VideoJob } from "@/lib/api";

const FORMATS = [
  { value: "reel_short", label: "Reel / Short (9:16, 1080x1920)" },
  { value: "youtube_main", label: "YouTube Main (16:9, 1920x1080)" },
];

export default function VideosPage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const [format, setFormat] = useState(FORMATS[0].value);
  const [jobs, setJobs] = useState<VideoJob[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function refreshJobs() {
    try {
      const data = await listVideoJobs();
      setJobs(data);
    } catch (err) {
      router.push("/login");
    }
  }

  useEffect(() => {
    refreshJobs();
    const interval = setInterval(refreshJobs, 4000);
    return () => clearInterval(interval);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createVideoJob(prompt, format);
      setPrompt("");
      await refreshJobs();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Could not create video job");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="container">
      <h2>Video Studio</h2>
      <div className="card">
        <form onSubmit={handleSubmit}>
          <textarea
            className="input"
            rows={4}
            placeholder="Describe the video you want to generate..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            required
          />
          <select className="input" value={format} onChange={(e) => setFormat(e.target.value)}>
            {FORMATS.map((f) => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>
          {error && <p className="error-text">{error}</p>}
          <button className="btn" type="submit" disabled={submitting}>
            {submitting ? "Submitting..." : "Generate Video"}
          </button>
        </form>
      </div>

      <h3>Your Jobs</h3>
      <div className="grid">
        {jobs.map((job) => (
          <div className="card" key={job.id}>
            <span className={`badge badge-${job.status}`}>{job.status}</span>
            <p>{job.prompt.slice(0, 80)}{job.prompt.length > 80 ? "..." : ""}</p>
            <p>Format: {job.format}</p>
            <p>Progress: {job.progress_percent}%</p>
            {job.output_url && <a href={job.output_url} target="_blank">View Output</a>}
            {job.error_message && <p className="error-text">{job.error_message}</p>}
          </div>
        ))}
        {jobs.length === 0 && <p>No video jobs yet.</p>}
      </div>
    </main>
  );
}
