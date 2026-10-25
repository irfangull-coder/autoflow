# AutoFlow Live Deploy Guide — Render (Backend) + Vercel (Frontend)

**Ye guide Roman Urdu me hai, step-by-step. Is me koi step skip mat karna, warna frontend backend se connect nahi hoga.**

## Pehle samajh lo: kya kahan chalega?

- **Vercel = Frontend sirf:** Dashboard (HTML/JS) yahan chalega. Vercel ka kaam sirf page dikhana hai.
- **Render = Backend:** FastAPI, agents, RAG, orders, approvals aur logs yahan chalenge.
- **Dono ka rabta:** Frontend `frontend/config.js` me Render ka URL likha hota hai, aur backend `ALLOWED_ORIGINS` me Vercel ki URL hoti hai. Ye dono ek doosre ko pehchante hain, tabhi browser data aane deta hai (CORS).

## Step 0 — Tayyari (5 minute)

1. GitHub account banao (agar nahi hai).
2. Is `autoflow` folder ko GitHub par naya repo banao, masalan `autoflow`.
3. Code push karo:
   ```bash
   cd autoflow
   git init
   git add .
   git commit -m "AutoFlow starter + Render/Vercel live setup"
   git branch -M main
   git remote add origin https://github.com/TUMHARA-USERNAME/autoflow.git
   git push -u origin main
   ```
   **Note:** `.gitignore` me `.venv/`, `autoflow.db` aur `__pycache__` pehle se ignore hain, wo GitHub par nahi jayen ge. Ye theek hai.

## Step 1 — Backend Render par lagao

1. https://render.com par jao, GitHub se login karo.
2. **New > Web Service** par click karo, apna `autoflow` repo chuno.
3. Settings ye rakho:
   - **Name:** `autoflow-api`
   - **Environment:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free (shuru ke liye theek hai)
   - **Health Check Path:** `/api/health`
   - **Environment Variable:** `ALLOWED_ORIGINS` = `https://TUMHARI-VERCEL-URL.vercel.app` (ye URL Step 2 ke baad mile gi, phir wapas aa kar yahan update karna hai)
4. **Create Web Service** dabao. Pehla deploy 2–5 minute le sakta hai.
5. Deploy complete hone par Render tumhe URL de ga, masalan:
   `https://autoflow-api.onrender.com`
6. Is URL ko browser me khol kar check karo:
   - `https://autoflow-api.onrender.com/api/health` par `{"ok": true}` aana chahiye.
   - Agar ye na aaye to Render ke **Logs** me error dekho, aage mat barho.

**Free plan ki sachai (pehle se jaan lo):**
- Free service kuch der use na ho to "so" jati hai. Pehla request 30–60 second late aa sakta hai, phir normal ho jata hai. Ye koi bug nahi, free plan ki limit hai.
- Free instance par restart/redeploy par SQLite file reset ho sakti hai. Demo ke liye ye theek hai, lekin asli data hamesha save rakhna hai to baad me ya to Render par persistent disk lagani hogi, ya database ko Postgres (Neon/Supabase free) par shift karna hoga. Is starter me `AUTOFLOW_DB_PATH` env var is liye rakha hai ke disk lagane par path `/data/autoflow.db` kar sako.

## Step 2 — Frontend Vercel par lagao

1. https://vercel.com par jao, GitHub se login karo.
2. **Add New > Project** par click karo, wahi `autoflow` repo chuno.
3. **Root Directory** me `frontend` likho aur select karo. Ye sabse zaroori step hai — agar root directory poora repo rakha to Vercel backend code ko bhi site samajh le ga aur ghalat deploy hoga.
4. **Framework Preset:** Other (koi framework nahi, sirf static HTML/JS hai).
5. **Deploy** dabao. Vercel tumhe URL de ga, masalan:
   `https://autoflow-demo.vercel.app`

## Step 3 — Dono ko joro (ye step bhoolna sabse aam ghalti hai)

1. **Frontend me Render URL dalo:**
   - `frontend/config.js` kholo.
   - `window.AUTOFLOW_API_URL = "https://autoflow-api.onrender.com";` likho (apni asli Render URL, aakhir me `/` nahi).
   - GitHub par push karo. Vercel khud dobara deploy kar de ga.
2. **Backend me Vercel URL dalo:**
   - Render par jao > apni service > **Environment**.
   - `ALLOWED_ORIGINS` ki value ko apni asli Vercel URL se badlo, masalan `https://autoflow-demo.vercel.app`.
   - Service ko **Manual Deploy > Deploy latest commit** se dobara deploy karo (env change par kabhi kabhi khud restart ho jata hai, kabhi manual chahiye hota hai).
3. **Dono URLs ko cross-check karo:**
   - Vercel site kholo, sawal poocho: `mera order 1023 kahan hai?`
   - Agar jawab aa gaya aur approval queue me draft aa gaya to live setup kamyab hai.

## Step 4 — Agar kaam na kare to kya check karna hai?

| Masla | Wajah aur hal |
|---|---|
| Dashboard khulta hai, jawab nahi aata | `config.js` me Render URL ghalat hai, ya aakhir me `/` laga hua hai. URL dobara check karo. |
| Browser console me CORS error | Render par `ALLOWED_ORIGINS` me Vercel ki URL nahi hai, ya spelling ghalat hai. Render env update karo aur redeploy karo. |
| Render URL par 404 ya app nahi khulti | Build fail hua hai. Render Logs dekho, aksar `requirements.txt` ya start command ki ghalti hoti hai. |
| Pehla request bahut slow hai | Render free plan so raha tha, 30–60 second wait karo, phir dobara try karo. Ye normal hai. |
| Approval approve kiya, dobara khola to ghaib | Free Render instance restart hua aur SQLite reset ho gaya. Demo ke liye dobara sawal poocho; asli persistence ke liye disk ya Postgres chahiye (Step 1 ki note dekho). |

## Step 5 — Live link supervisor / portfolio me kaise dikhana hai?

- Vercel link: Dashboard ka link (yehi log kholen ge).
- Render link: Sirf API ka link, isko `/api/health` ke sath dikhana, taake pata chale backend zinda hai.
- GitHub repo ka link bhi sath rakho, taake code bhi dekha ja sake.

## Files jo is live setup ke liye add/change hui hain

- `backend/main.py` — CORS + `/api/health` endpoint
- `backend/store.py` — `AUTOFLOW_DB_PATH` env var se DB path
- `frontend/config.js` — **Nayi file**, sirf yahan Render URL badalni hai
- `frontend/index.html` — Saare API calls ab `config.js` wali base URL se hote hain
- `Dockerfile` — Render Docker deploy ke liye (optional, native Python plan bhi kaam karta hai)
- `render.yaml` — Render Blueprint settings
- `DEPLOY_RENDER_VERCEL.md` — Ye guide
