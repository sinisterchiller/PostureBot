# PostureBot (SillyCon)

## Overview

PostureBot is an interactive "Game Hub" that uses a webcam and MediaPipe for pose/head tracking. It features two interactive games:

- **Traffic Rush** – A driving game where you move the car with head tilts.
- **Tilt Master (Head Tilt Quiz)** – A quiz game where you answer by tilting your head left or right.

The system combines:

- A Next.js web UI for selecting games and modes
- A Python orchestration backend that starts/stops games and monitors posture
- OpenCV + MediaPipe for camera and pose detection
- Pygame for the traffic game
- External APIs (Open Trivia DB, Chuck Norris, Dad Jokes, etc.) for quiz content
- Police mode and easy access to game switching and cancellation

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js, Port 3000)                            │
│  • Game Hub UI                                                              │
│  • SillyTilter mascot                                                       │
│  • Calls neazbackend at 127.0.0.1:2301                                      │
└────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                    NEAZ BACKEND (FastAPI, Port 2301)                        │
│  • Central orchestrator                                                     │
│  • POST /game  → Launch Traffic Rush (0) or Tilt Master (1)                 │
│  • POST /mode  → Enable/disable Police Mode (posture monitoring)            │
│  • POST /close → Stop all games & monitoring                                │
└────────────────────────────────────────────────────────────────────────────┘
          │                              │
          ▼                              ▼
┌──────────────────────────────┐   ┌──────────────────────────────────────────┐
│   TRAFFIC RUSH (Game 0)      │   │   TILT MASTER (Game 1)                   │
│   ─────────────────────      │   │   ────────────────────                   │
│   • koushikbackend (8000)    │   │   • ishayatbackend (7000)                │
│   • trafficgame.py (Pygame)  │   │   • headtilt_game.py (OpenCV + MediaPipe)│
│   • posturetest_koushik.py   │   │     - Head tilt detection                │
│     (camera → pyautogui)     │   │     - Quiz UI via camera overlay         │
└──────────────────────────────┘   └──────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│   POLICE MODE (Mode 1)                                                       │
│   ───────────────────                                                       │
│   • posturemonitor.py                                                        │
│   • koushikbackend (8000)                                                    │
│   • Monitors posture                                                         │
│   • After 5s bad posture → launches Traffic Rush or Tilt Master              │
└─────────────────────────────────────────────────────────────────────────────┘
```

> **Note:** neazbackend must be started with `--port 2301` so the frontend can reach it.

## Project Structure

```
PostureBot/
├── frontend/                    # Next.js app (main UI)
│   ├── app/
│   │   ├── page.tsx            # Game Hub page
│   │   ├── layout.tsx          # Root layout + fonts
│   │   └── globals.css         # Tailwind + theme variables
│   ├── components/
│   │   ├── silly-tilter.tsx    # Animated mascot
│   │   ├── toaster-wrapper.tsx
│   │   └── ui/                 # shadcn/ui components
│   └── package.json
│
├── neazbackend.py              # Main orchestrator (port 2301)
├── koushikbackend.py           # Traffic Rush backend (port 8000)
├── ishayatbackend.py           # Tilt Master backend (port 7000)
│
├── gamekoushik/                # Traffic Rush stack
│   ├── trafficgame.py          # Pygame driving game
│   ├── posturetest_koushik.py  # Camera → head tilt → pyautogui
│   └── pose_landmarker_full.task
│
├── gameishayat/                # Tilt Master stack
│   ├── headtilt_game.py        # Camera + quiz overlay + head control
│   └── pose_landmarker_full.task
│
└── consequence/                # Police Mode
    ├── posturemonitor.py       # Posture monitoring process
    └── pose_landmarker_full.task
```

## Component Deep Dive

### 1. Frontend (`frontend/`)

**Stack:** Next.js 16, React 19, Tailwind, Radix UI (shadcn/ui), Bangers & Comic Neue fonts

**Main page (`app/page.tsx`):**

- Two game cards: Traffic Rush (game 0) and Tilt Master (game 1)
- Police Mode – enables posture monitoring and auto-launches games
- Close All – stops monitoring and games
- Calls `http://127.0.0.1:2301` for `/game`, `/mode`, `/close`
- Easter egg: choosing Tilt Master triggers a Rick Roll overlay before launching

**SillyTilter (`components/silly-tilter.tsx`):**

- Animated mascot that tilts, bounces, and waves
- Messages change with hover/loading/active game
- Extra motion when Tilt Master is active

### 2. Neaz Backend (`neazbackend.py`)

Central orchestrator that spawns and kills processes.

| Endpoint  | Method | Body              | Action                   |
|-----------|--------|-------------------|--------------------------|
| `/health` | GET    | -                 | Returns `{"health": "ok"}` |
| `/game`   | POST   | `{"game": 0 \| 1}`| Launch game 0 or 1       |
| `/mode`   | POST   | `{"mode": 0 \| 1}`| Disable/enable Police Mode |
| `/close`  | POST   | `{"close": 1}`    | Stop everything          |

**Game 0 (Traffic Rush):**

- Kills: posturemonitor, koushikbackend, headtilt_game, posturetest_koushik, trafficgame, ishayatbackend
- Starts: trafficgame.py, posturetest_koushik.py, koushikbackend (port 8000)

**Game 1 (Tilt Master):**

- Same kill sequence
- Starts: headtilt_game.py, ishayatbackend (port 7000)

**Mode 1 (Police Mode):**

- Kills all game-related processes
- Starts: posturemonitor.py, koushikbackend (port 8000)

> **Note:** Run neazbackend with `uvicorn neazbackend:api --port 2301` so the frontend can connect.

### 3. Traffic Rush Stack

**`gamekoushik/trafficgame.py`:**

- Pygame lane-based driving game
- Dodge cars by moving left/right (A/D or arrow keys)
- Pyautogui simulates key presses; posturetest_koushik.py provides head-based input

**`gamekoushik/posturetest_koushik.py`:**

- Uses MediaPipe pose landmarks (nose, shoulders, ears, eyes)
- Sends `POST /posturemetrics` to koushikbackend with:
  - headdirection_left, headdirection_right (tilt > 15°)
  - headtiltangle, severity, confidence
- Runs continuously and does not render its own UI

**`koushikbackend.py`:**

- `POST /posturemetrics` – receives pose data, triggers `pyautogui.press("left")` or `pyautogui.press("right")` (with ~0.7s cooldown)
- `POST /consequence` – used by posturemonitor to detect bad posture and launch Traffic Rush after 5 seconds

### 4. Tilt Master Stack

**`gameishayat/headtilt_game.py`:**

- Uses MediaPipe pose landmarks to compute head tilt from ear positions
- SimpleTiltSelector – 5-frame smoothing; left/right if tilt > 15°; hold ~0.7s to "lock"
- Draws quiz UI as OpenCV overlay on the camera feed
- Modes: random, trivia, chuck, dadjokes, facts, wouldyourather, riddles, jokes, neverhaveiever
- Keyboard: s/t/c/d/f/w/r/j/n for modes, Space to confirm, p to pause, e to exit, q to quit
- Sends tilt data to `POST http://127.0.0.1:7000/headtilt`
- Calls ishayatbackend for: start game, next question, submit answer, stats, end game

**`ishayatbackend.py`:**

- `POST /headtilt` – stores latest tilt from headtilt_game
- `GET /headtilt` – returns current tilt
- `/game/start`, `/game/next`, `/game/answer`, `/game/stats`, `/game/end` – quiz flow and scoring
- Fetches questions from Open Trivia DB, Chuck Norris API, Dad Jokes, etc.

### 5. Police Mode

**`consequence/posturemonitor.py`:**

- Uses MediaPipe to detect posture from nose, shoulders, ears
- Sends `POST http://127.0.0.1:8000/consequence` with:
  - POSTURE_BAD or POSTURE_OK
  - severity, headtiltangle, headdirection_left/right

**`koushikbackend`'s /consequence handler:**

- Tracks bad-posture time
- After 5 seconds, triggers a game launch via `POST http://127.0.0.1:2301/game` with `{"game": 0}` or `{"game": 1}`

## Data Flow Examples

### Traffic Rush

1. User clicks "Traffic Rush" → frontend `POST /game` with `{"game": 0}`
2. neazbackend starts trafficgame, posturetest_koushik, koushikbackend
3. posturetest_koushik streams pose data → `POST /posturemetrics` → koushikbackend
4. koushikbackend calls `pyautogui.press("left")` or `pyautogui.press("right")`
5. Traffic Rush receives these key presses and moves the car

### Tilt Master

1. User clicks "Tilt Master" → frontend `POST /game` with `{"game": 1}` → Rick Roll overlay → launch
2. neazbackend starts headtilt_game and ishayatbackend
3. headtilt_game sends tilt data to `POST /headtilt`, gets questions from ishayatbackend
4. User tilts head left/right, holds ~0.7s, then presses Space
5. Answer submitted to ishayatbackend; scoring and next question handled there

### Police Mode

1. User enables Police Mode → frontend `POST /mode` with `{"mode": 1}`
2. neazbackend starts posturemonitor and koushikbackend
3. posturemonitor sends posture status → `POST /consequence`
4. After 5s of bad posture, koushikbackend calls neazbackend to launch Traffic Rush or Tilt Master

## Port Summary

| Service          | Port | Notes                          |
|------------------|------|--------------------------------|
| neazbackend      | 2301 | Must be started with --port 2301 |
| koushikbackend   | 8000 | Default uvicorn                |
| ishayatbackend   | 7000 | Spawned with --port 7000       |
| Next.js frontend | 3000 | `next dev` default             |

## Dependencies

**Python (from requirements):**

- fastapi, mediapipe, requests, pygame, pyautogui, pydantic, uvicorn

**MediaPipe models:**

- `pose_landmarker_full.task` in:
  - gameishayat/
  - gamekoushik/
  - consequence/

> Can be obtained from the [MediaPipe pose landmarker model](https://developers.google.com/mediapipe/solutions/vision/pose_landmarker).

## Run Order

1. Create virtual environment and install Python dependencies
2. Ensure `pose_landmarker_full.task` is in the three directories above
3. Start neazbackend: `uvicorn neazbackend:api --reload --port 2301`
4. Start frontend: `cd frontend && pnpm dev` (or `npm run dev --legacy-peer-deps` if needed)
5. Use the web UI to choose games or enable Police Mode

## Platform Notes

- **Paths:** `.venv/bin/python` implies a Unix-style environment; on Windows, use `.venv\Scripts\python.exe` and adjust subprocess commands.
- **Process management:** `pkill` commands in neazbackend are Unix-specific; Windows would need different process management.
- **Traffic game:** Uses keyboard input and must be focused to receive pyautogui presses.
