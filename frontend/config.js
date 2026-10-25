// AutoFlow frontend config — Vercel deploy ke liye YEHI EK JAGAH BADLO.
//
// Local run (Render backend nahi, apna laptop):
//   window.AUTOFLOW_API_URL = "";
//   (khaali ho to dashboard relative /api/... use kare ga, jo local
//    FastAPI server aur Render full-stack dono par chalta hai)
//
// Live run (Frontend Vercel par, Backend Render par):
//   window.AUTOFLOW_API_URL = "https://autoflow-api.onrender.com";
//   Apni Render service ka asli URL yahan likho, aakhir me "/" NA lagao.
//   Phir Vercel par dobara deploy karo (ya GitHub push karo, auto-deploy
//   ho jayega). Backend par ALLOWED_ORIGINS me apni Vercel URL bhi
//   add karna mat bhoolna, warna browser CORS error de ga.
window.AUTOFLOW_API_URL = "https://autoflow-api-fqns.onrender.com";
