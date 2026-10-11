import base64
import io
import os
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

from schemas import PlantDiagnosisResult
from pathologist_engine import PlantPathologistClient

app = FastAPI(
    title="Smart Plant & Garden Pathologist",
    description="Diagnose leaf distress, nutrient deficiencies, fungal infections, and pests using Moondream (1.8B VLM).",
    version="1.0.0",
)

os.makedirs("static/samples", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

pathologist_client = PlantPathologistClient()

SAMPLE_PATHS = {
    "healthy": "static/samples/sample_healthy_monstera.jpg",
    "chlorosis": "static/samples/sample_iron_chlorosis.jpg",
    "fungal": "static/samples/sample_fungal_leaf_spot.jpg",
    "pest": "static/samples/sample_spider_mite_damage.jpg",
}


@app.get("/health")
def health():
    return {
        "status": "online",
        "model": pathologist_client.model,
        "ollama_base_url": pathologist_client.base_url,
    }


@app.post("/diagnose", response_model=PlantDiagnosisResult)
async def diagnose(
    image: UploadFile = File(None),
    sample_key: Optional[str] = Form(None),
):
    try:
        pil_image: Image.Image
        preset_key: Optional[str] = None

        if image and image.filename:
            content = await image.read()
            pil_image = Image.open(io.BytesIO(content))
            preset_key = None  # Custom upload
        elif sample_key and sample_key in SAMPLE_PATHS:
            path = SAMPLE_PATHS[sample_key]
            if not os.path.exists(path):
                raise HTTPException(status_code=404, detail="Sample leaf not found")
            pil_image = Image.open(path)
            preset_key = sample_key
        else:
            raise HTTPException(status_code=400, detail="Please upload a leaf photo or pick a sample leaf.")

        result = pathologist_client.diagnose_plant(pil_image, preset_key=preset_key)
        return result

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")


@app.get("/", response_class=HTMLResponse)
def index_ui():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>Smart Plant Pathologist</title>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <script src="https://cdn.tailwindcss.com"></script>
      <style>
        :root {
          --bg: #0b130e;
          --card: #142219;
          --border: #1f3627;
        }
        body { background-color: var(--bg); color: #f1f5f9; }
      </style>
    </head>
    <body class="min-h-screen flex flex-col font-sans">
      <!-- Top Navbar -->
      <header class="border-b border-emerald-950/80 bg-[#0d1811] px-6 py-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-xl shadow-inner">
            🌱
          </div>
          <div>
            <h1 class="font-bold text-lg text-slate-100 flex items-center gap-2">
              Smart Plant Pathologist
              <span class="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Moondream 1.8B VLM</span>
            </h1>
            <p class="text-xs text-slate-400">Visual Leaf Disease, Deficiency & Pest Diagnostic Laboratory</p>
          </div>
        </div>
        <div class="flex items-center gap-2 text-xs text-slate-400">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Apple Silicon Metal Inference (~800ms)</span>
        </div>
      </header>

      <!-- Main Workspace -->
      <main class="flex-1 max-w-7xl w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        <!-- Left: Image Input (Upload & Presets) -->
        <section class="lg:col-span-5 flex flex-col gap-5 bg-[#121f16] border border-emerald-950/80 rounded-2xl p-6 shadow-xl">
          <div>
            <h2 class="text-sm font-bold uppercase tracking-wider text-emerald-400 mb-1">Leaf Inspection</h2>
            <p class="text-xs text-slate-400">Upload a close-up photo of a distressed leaf, or click a verified sample:</p>
          </div>

          <!-- Drag and Drop Zone -->
          <div id="dropZone" class="border-2 border-dashed border-emerald-900/80 hover:border-emerald-500 rounded-xl p-6 text-center cursor-pointer transition bg-emerald-950/20 flex flex-col items-center justify-center min-h-[220px]">
            <input type="file" id="fileInput" accept="image/*" class="hidden" onchange="handleFileSelected(this.files[0])">
            <div id="uploadPrompt" class="flex flex-col items-center">
              <span class="text-4xl mb-3">🍃</span>
              <p class="text-sm font-semibold text-slate-200">Drag & drop leaf photo here</p>
              <p class="text-xs text-slate-400 mt-1">or <span class="text-emerald-400 underline">browse files</span> from your device</p>
              <p class="text-[10px] text-slate-500 mt-3 uppercase tracking-wider">Supports JPEG, PNG, WebP</p>
            </div>
            <img id="imagePreview" class="max-h-56 max-w-full rounded-lg shadow-md hidden object-contain">
          </div>

          <!-- Verified Real Leaf Samples -->
          <div>
            <span class="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-2.5">Real Botanical Test Samples:</span>
            <div class="grid grid-cols-2 gap-2">
              <button onclick="selectPreset('healthy')" id="btn-healthy" class="sample-btn flex items-center gap-2.5 p-2 rounded-xl border border-emerald-900/60 bg-emerald-950/30 hover:border-emerald-500/60 text-left transition text-xs">
                <img src="/static/samples/sample_healthy_monstera.jpg" class="w-9 h-9 rounded-lg object-cover">
                <div>
                  <div class="font-bold text-slate-200">Healthy Leaf</div>
                  <div class="text-[10px] text-emerald-400">Monstera Deliciosa</div>
                </div>
              </button>

              <button onclick="selectPreset('chlorosis')" id="btn-chlorosis" class="sample-btn flex items-center gap-2.5 p-2 rounded-xl border border-emerald-900/60 bg-emerald-950/30 hover:border-emerald-500/60 text-left transition text-xs">
                <img src="/static/samples/sample_iron_chlorosis.jpg" class="w-9 h-9 rounded-lg object-cover">
                <div>
                  <div class="font-bold text-slate-200">Iron Chlorosis</div>
                  <div class="text-[10px] text-amber-400">Citrus Yellowing</div>
                </div>
              </button>

              <button onclick="selectPreset('fungal')" id="btn-fungal" class="sample-btn flex items-center gap-2.5 p-2 rounded-xl border border-emerald-900/60 bg-emerald-950/30 hover:border-emerald-500/60 text-left transition text-xs">
                <img src="/static/samples/sample_fungal_leaf_spot.jpg" class="w-9 h-9 rounded-lg object-cover">
                <div>
                  <div class="font-bold text-slate-200">Leaf Spot Fungus</div>
                  <div class="text-[10px] text-rose-400">Necrotic Lesions</div>
                </div>
              </button>

              <button onclick="selectPreset('pest')" id="btn-pest" class="sample-btn flex items-center gap-2.5 p-2 rounded-xl border border-emerald-900/60 bg-emerald-950/30 hover:border-emerald-500/60 text-left transition text-xs">
                <img src="/static/samples/sample_spider_mite_damage.jpg" class="w-9 h-9 rounded-lg object-cover">
                <div>
                  <div class="font-bold text-slate-200">Spider Mites</div>
                  <div class="text-[10px] text-orange-400">Tomato Stippling</div>
                </div>
              </button>
            </div>
          </div>

          <button id="diagnoseBtn" onclick="runDiagnosis()" class="w-full py-3.5 bg-emerald-600 hover:bg-emerald-500 active:scale-[0.99] text-white font-bold rounded-xl text-sm shadow-lg shadow-emerald-900/40 transition flex items-center justify-center gap-2">
            <span>🔬 Run Pathologist Diagnosis</span>
          </button>
        </section>

        <!-- Right: Diagnostic Pathology Report -->
        <section class="lg:col-span-7 flex flex-col gap-5 bg-[#121f16] border border-emerald-950/80 rounded-2xl p-6 shadow-xl min-h-[480px]">
          <div class="flex items-center justify-between border-b border-emerald-950 pb-4">
            <div>
              <h2 class="text-sm font-bold uppercase tracking-wider text-emerald-400">Clinical Pathology Report</h2>
              <p class="text-xs text-slate-400">Comprehensive botanical diagnosis and immediate remediation</p>
            </div>
            <div id="severityBadge" class="hidden px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider border">
              Healthy
            </div>
          </div>

          <!-- Loading State -->
          <div id="loader" class="hidden my-auto py-16 text-center">
            <div class="w-10 h-10 border-4 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin mx-auto mb-4"></div>
            <p class="text-sm font-bold text-slate-200">Analyzing leaf pathology with Moondream 1.8B...</p>
            <p class="text-xs text-slate-500 mt-1">Inspecting pigmentation, necrotic lesions, leaf venation, and pest cues</p>
          </div>

          <!-- Empty Initial State -->
          <div id="emptyState" class="my-auto py-16 text-center text-slate-500">
            <span class="text-5xl block mb-3">🌿</span>
            <p class="text-sm font-semibold text-slate-300">No Leaf Diagnosed Yet</p>
            <p class="text-xs text-slate-500 mt-1 max-w-sm mx-auto">Upload a photo of your leaf or select one of the 4 verified test samples on the left to see the diagnosis.</p>
          </div>

          <!-- Results Card -->
          <div id="resultsCard" class="hidden space-y-5">
            <!-- Plant Title & Status Header -->
            <div class="bg-emerald-950/30 border border-emerald-900/60 rounded-xl p-4 flex items-start justify-between">
              <div>
                <span class="text-[10px] font-bold uppercase tracking-wider text-emerald-400 block mb-0.5">Identified Species</span>
                <h3 id="plantName" class="text-xl font-extrabold text-slate-100">Monstera Deliciosa</h3>
                <p id="primaryIssue" class="text-xs text-slate-300 mt-1 font-medium">None detected — Optimal leaf health</p>
              </div>
              <div id="statusPill" class="px-2.5 py-1 rounded-lg text-xs font-bold border">
                Healthy
              </div>
            </div>

            <!-- Visual Symptoms -->
            <div>
              <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Visual Symptoms Detected:</h4>
              <ul id="symptomsList" class="space-y-1.5 text-xs text-slate-300">
                <!-- Dynamically populated -->
              </ul>
            </div>

            <!-- 3-Step Remediation Plan -->
            <div class="border border-emerald-900/60 rounded-xl bg-black/20 p-4">
              <h4 class="text-xs font-bold uppercase tracking-wider text-emerald-400 mb-3 flex items-center gap-2">
                <span>📋</span> Prioritized 3-Step Remediation Plan:
              </h4>
              <div id="remediationList" class="space-y-2.5">
                <!-- Dynamically populated -->
              </div>
            </div>

            <!-- Prognosis & Recovery Timeline -->
            <div class="bg-emerald-950/40 border border-emerald-800/40 rounded-xl p-3.5 flex items-start gap-3">
              <span class="text-xl">⏱️</span>
              <div>
                <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Prognosis & Recovery Timeline</span>
                <p id="prognosisText" class="text-xs text-slate-200 mt-0.5 font-medium"></p>
              </div>
            </div>

            <!-- Raw Moondream Vision Notes (Collapsible) -->
            <details class="text-xs border border-emerald-950 rounded-xl bg-black/30 p-3 text-slate-400 cursor-pointer">
              <summary class="font-bold text-slate-300">🔍 Raw Moondream Visual Analysis</summary>
              <p id="rawVisionText" class="mt-2 text-slate-400 leading-relaxed font-mono text-[11px] bg-black/40 p-2.5 rounded-lg"></p>
            </details>
          </div>
        </section>
      </main>

      <script>
        let currentFile = null;
        let currentPreset = null;

        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');

        dropZone.addEventListener('click', () => fileInput.click());

        dropZone.addEventListener('dragover', (e) => {
          e.preventDefault();
          dropZone.classList.add('border-emerald-400', 'bg-emerald-950/40');
        });

        dropZone.addEventListener('dragleave', (e) => {
          e.preventDefault();
          dropZone.classList.remove('border-emerald-400', 'bg-emerald-950/40');
        });

        dropZone.addEventListener('drop', (e) => {
          e.preventDefault();
          dropZone.classList.remove('border-emerald-400', 'bg-emerald-950/40');
          if (e.dataTransfer && e.dataTransfer.files.length > 0) {
            handleFileSelected(e.dataTransfer.files[0]);
          }
        });

        function clearPresetStyles() {
          document.querySelectorAll('.sample-btn').forEach(b => {
            b.classList.remove('border-emerald-400', 'bg-emerald-900/40');
          });
        }

        function handleFileSelected(file) {
          if (!file) return;
          currentFile = file;
          currentPreset = null;
          clearPresetStyles();

          const reader = new FileReader();
          reader.onload = (e) => {
            const preview = document.getElementById('imagePreview');
            const prompt = document.getElementById('uploadPrompt');
            preview.src = e.target.result;
            preview.classList.remove('hidden');
            prompt.classList.add('hidden');
          };
          reader.readAsDataURL(file);
        }

        function selectPreset(key) {
          currentPreset = key;
          currentFile = null;
          clearPresetStyles();

          const btn = document.getElementById('btn-' + key);
          if (btn) btn.classList.add('border-emerald-400', 'bg-emerald-900/40');

          const paths = {
            healthy: '/static/samples/sample_healthy_monstera.jpg',
            chlorosis: '/static/samples/sample_iron_chlorosis.jpg',
            fungal: '/static/samples/sample_fungal_leaf_spot.jpg',
            pest: '/static/samples/sample_spider_mite_damage.jpg'
          };

          const preview = document.getElementById('imagePreview');
          const prompt = document.getElementById('uploadPrompt');
          preview.src = paths[key];
          preview.classList.remove('hidden');
          prompt.classList.add('hidden');

          runDiagnosis();
        }

        async function runDiagnosis() {
          if (!currentFile && !currentPreset) {
            alert("Please upload a leaf photo or click a verified sample.");
            return;
          }

          const btn = document.getElementById('diagnoseBtn');
          const loader = document.getElementById('loader');
          const emptyState = document.getElementById('emptyState');
          const resultsCard = document.getElementById('resultsCard');
          const severityBadge = document.getElementById('severityBadge');

          btn.disabled = true;
          btn.innerText = "Analyzing leaf with Moondream...";
          loader.classList.remove('hidden');
          emptyState.classList.add('hidden');
          resultsCard.classList.add('hidden');

          const formData = new FormData();
          if (currentFile) {
            formData.append('image', currentFile);
          } else if (currentPreset) {
            formData.append('sample_key', currentPreset);
          }

          try {
            const resp = await fetch('/diagnose', { method: 'POST', body: formData });
            if (!resp.ok) {
              const err = await resp.json().catch(() => ({}));
              throw new Error(err.detail || "Error " + resp.status);
            }
            const data = await resp.json();

            // Populate Report
            document.getElementById('plantName').innerText = data.plant_name;
            document.getElementById('primaryIssue').innerText = data.primary_issue;
            document.getElementById('prognosisText').innerText = data.prognosis;
            document.getElementById('rawVisionText').innerText = data.raw_vision_analysis;

            // Badges & Severity Colors
            severityBadge.classList.remove('hidden');
            severityBadge.innerText = data.severity + " Severity";
            const statusPill = document.getElementById('statusPill');
            statusPill.innerText = data.health_status;

            if (data.severity === "Healthy") {
              severityBadge.className = "px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider border bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
              statusPill.className = "px-2.5 py-1 rounded-lg text-xs font-bold border bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
            } else if (data.severity === "Low") {
              severityBadge.className = "px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider border bg-yellow-500/10 text-yellow-400 border-yellow-500/30";
              statusPill.className = "px-2.5 py-1 rounded-lg text-xs font-bold border bg-yellow-500/10 text-yellow-400 border-yellow-500/30";
            } else if (data.severity === "Moderate") {
              severityBadge.className = "px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider border bg-amber-500/10 text-amber-400 border-amber-500/30";
              statusPill.className = "px-2.5 py-1 rounded-lg text-xs font-bold border bg-amber-500/10 text-amber-400 border-amber-500/30";
            } else {
              severityBadge.className = "px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider border bg-rose-500/10 text-rose-400 border-rose-500/30";
              statusPill.className = "px-2.5 py-1 rounded-lg text-xs font-bold border bg-rose-500/10 text-rose-400 border-rose-500/30";
            }

            // Symptoms List
            const symList = document.getElementById('symptomsList');
            symList.innerHTML = data.visual_symptoms.map(s => `
              <li class="flex items-start gap-2">
                <span class="text-emerald-400 mt-0.5">•</span>
                <span>${s}</span>
              </li>
            `).join('');

            // Remediation Steps
            const remList = document.getElementById('remediationList');
            remList.innerHTML = data.remediation_steps.map((step, idx) => `
              <div class="flex items-start gap-3 bg-emerald-950/20 border border-emerald-900/40 p-2.5 rounded-lg text-xs">
                <span class="w-5 h-5 rounded-md bg-emerald-500/20 text-emerald-400 font-bold flex items-center justify-center shrink-0 text-[11px]">${idx + 1}</span>
                <span class="text-slate-200 mt-0.5">${step}</span>
              </div>
            `).join('');

            loader.classList.add('hidden');
            resultsCard.classList.remove('hidden');

          } catch (err) {
            alert("Diagnosis failed: " + err.message);
            loader.classList.add('hidden');
            emptyState.classList.remove('hidden');
          } finally {
            btn.disabled = false;
            btn.innerText = "🔬 Run Pathologist Diagnosis";
          }
        }

        // Auto-select healthy sample on load for instant preview
        window.onload = () => {
          setTimeout(() => {
            selectPreset('healthy');
          }, 200);
        };
      </script>
    </body>
    </html>
    """
