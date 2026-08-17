// Process supervisor for the live trial -- backend crashes/exits are
// otherwise unrecoverable until someone notices and manually restarts it
// (this is what caused the 2026-08-17 "site is down" incident: the process
// simply wasn't running, with nothing to bring it back).
//
// Usage:
//   pm2 start ecosystem.config.js   -- start both, auto-restart on crash
//   pm2 status                      -- check they're up
//   pm2 logs                        -- tail both processes' output
//   pm2 restart all                 -- manual restart
//   pm2 stop all                    -- stop both
//
// JWT_SECRET/DATABASE_URL/etc come from .env via config.py's load_dotenv()
// as usual -- this file does not set or override any of them.
module.exports = {
  apps: [
    {
      name: "elite-backend",
      cwd: __dirname,
      script: ".venv/Scripts/python.exe",
      args: "-m uvicorn api.main:app --host 0.0.0.0 --port 8000",
      autorestart: true,
      max_restarts: 20,
      restart_delay: 3000,
      out_file: "logs/pm2-backend.out.log",
      error_file: "logs/pm2-backend.err.log",
    },
    {
      name: "elite-frontend",
      cwd: __dirname + "/frontend",
      script: "npm.cmd",
      args: "run dev -- --host",
      autorestart: true,
      max_restarts: 20,
      restart_delay: 3000,
      out_file: "../logs/pm2-frontend.out.log",
      error_file: "../logs/pm2-frontend.err.log",
    },
  ],
};
