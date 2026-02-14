'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { SillyTilter } from '@/components/silly-tilter'
import { Gamepad2, Users, ShieldAlert } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

export default function Page() {
  const [loading, setLoading] = useState<number | null>(null)
  const [hoveredGame, setHoveredGame] = useState<number | null>(null)
  const [policeModeEnabled, setPoliceModeEnabled] = useState(false)
  const [activeGame, setActiveGame] = useState<number | null>(null)
  const [showRickRoll, setShowRickRoll] = useState(false)
  const { toast } = useToast()

  const launchGame = async (gameId: number, triggeredByPolice = false) => {
    if (gameId === 1 && !triggeredByPolice) {
      setShowRickRoll(true)
      toast({
        title: 'GET RICKROLLED!',
        description: 'Never gonna give you up, never gonna let you down!',
      })
      setTimeout(() => {
        setShowRickRoll(false)
        actuallyLaunchGame(gameId, triggeredByPolice)
      }, 3000)
      return
    }
    actuallyLaunchGame(gameId, triggeredByPolice)
  }

  const actuallyLaunchGame = async (gameId: number, triggeredByPolice = false) => {
    setLoading(gameId)
    setActiveGame(gameId)
    try {
      const response = await fetch('http://127.0.0.1:2301/game', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ game: gameId }),
      })
      if (!response.ok) throw new Error('Failed to launch game')
      const data = await response.json()
      toast({
        title: triggeredByPolice ? 'POLICE MODE ACTIVATED!' : 'Game Launched!',
        description: triggeredByPolice
          ? 'Bad posture detected! Time to fix it with Traffic Rush!'
          : `${gameId === 0 ? 'Traffic Rush' : 'Tilt Master'} is starting...`,
        variant: triggeredByPolice ? 'destructive' : 'default',
      })
    } catch (error) {
      console.error('[v0] Error launching game:', error)
      toast({
        title: 'Error',
        description: 'Failed to launch game. Make sure the backend is running on port 2301.',
        variant: 'destructive',
      })
    } finally {
      setLoading(null)
    }
  }

  const handleBadPosture = () => {
    if (policeModeEnabled) {
      const randomGame = Math.floor(Math.random() * 2)
      launchGame(randomGame, true)
    }
  }

  const setPoliceMode = async (enabled: boolean) => {
    const newMode = enabled ? 1 : 0
    try {
      const response = await fetch('http://127.0.0.1:2301/mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: newMode }),
      })
      if (!response.ok) throw new Error('Mode request failed')
      setPoliceModeEnabled(enabled)
      toast({
        title: enabled ? 'Police Mode ON' : 'Police Mode OFF',
        description: enabled ? 'Camera & posture monitoring active!' : 'Monitoring disabled.',
      })
    } catch (error) {
      console.error('Failed to set police mode:', error)
      toast({
        title: 'Connection Error',
        description: 'Could not reach backend at 127.0.0.1:2301. Is neazbackend running?',
        variant: 'destructive',
      })
    }
  }

  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).triggerBadPostureGame = handleBadPosture
    }
  }, [policeModeEnabled])

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 flex items-center justify-center p-4">
      {showRickRoll && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="text-center space-y-6 animate-in zoom-in duration-500">
            <img
              src="https://media.tenor.com/x8v1oNUduSUAAAAC/rickroll-roll.gif"
              alt="Rick Roll"
              className="w-96 h-96 rounded-3xl shadow-2xl border-4 border-primary"
            />
            <h2 className="text-6xl font-display text-primary animate-pulse">
              YOU JUST GOT RICKROLLED!
            </h2>
            <p className="text-2xl text-primary-foreground">
              Loading Tilt Master...
            </p>
          </div>
        </div>
      )}

      <div className="w-full max-w-4xl space-y-12">
        <div className="text-center space-y-4">
          <h1 className="text-6xl md:text-7xl font-display text-balance bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent drop-shadow-lg tracking-wider transform hover:scale-105 transition-transform">
            GAME HUB!
          </h1>
          <p className="text-2xl md:text-3xl font-bold text-muted-foreground animate-pulse">
            Pick Your Epic Adventure!
          </p>
        </div>

        <div className="flex justify-center">
          <Button
            onClick={() => setPoliceMode(!policeModeEnabled)}
            variant={policeModeEnabled ? 'destructive' : 'outline'}
            size="lg"
            className={`font-display text-xl tracking-wider transition-all ${
              policeModeEnabled
                ? 'bg-destructive text-destructive-foreground animate-pulse shadow-2xl shadow-destructive/50'
                : 'hover:scale-105'
            }`}
          >
            <ShieldAlert className="w-6 h-6 mr-2" />
            {policeModeEnabled ? 'POLICE MODE: ON' : 'ACTIVATE POLICE MODE'}
          </Button>
        </div>

        <div className="flex justify-center">
          <SillyTilter
            gameHovered={hoveredGame}
            gameLoading={loading}
            activeGame={activeGame}
          />
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <Card
            className="group relative overflow-hidden border-4 border-primary/30 hover:border-primary transition-all duration-300 hover:shadow-2xl hover:shadow-primary/40 hover:scale-105 cursor-pointer bg-gradient-to-br from-card to-primary/5"
            onMouseEnter={() => setHoveredGame(0)}
            onMouseLeave={() => setHoveredGame(null)}
          >
            <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-secondary/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 rounded-full blur-3xl group-hover:bg-primary/20 transition-all" />
            <div className="relative p-8 space-y-6">
              <div className="flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-br from-primary to-secondary group-hover:scale-110 transition-transform shadow-lg">
                <Gamepad2 className="w-10 h-10 text-primary-foreground" />
              </div>
              <div className="space-y-3">
                <h2 className="text-3xl font-display text-foreground tracking-wide">
                  TRAFFIC RUSH!
                </h2>
                <p className="text-foreground/80 leading-relaxed text-lg font-semibold">
                  Dodge cars while keeping your posture perfect! Use your HEAD to steer! Beep beep!
                </p>
              </div>
              <Button
                onClick={() => {
                  launchGame(0)
                  setActiveGame(0)
                }}
                disabled={loading !== null}
                className="w-full h-16 text-2xl font-display tracking-wider bg-gradient-to-r from-primary via-secondary to-primary hover:scale-105 active:scale-95 transition-all shadow-xl hover:shadow-2xl disabled:opacity-50"
                size="lg"
              >
                {loading === 0 ? (
                  <span className="flex items-center gap-3">
                    <span className="w-6 h-6 border-4 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                    STARTING...
                  </span>
                ) : (
                  'PLAY NOW!'
                )}
              </Button>
            </div>
          </Card>

          <Card
            className="group relative overflow-hidden border-4 border-accent/30 hover:border-accent transition-all duration-300 hover:shadow-2xl hover:shadow-accent/40 hover:scale-105 cursor-pointer bg-gradient-to-br from-card to-accent/5"
            onMouseEnter={() => setHoveredGame(1)}
            onMouseLeave={() => setHoveredGame(null)}
          >
            <div className="absolute inset-0 bg-gradient-to-br from-accent/20 to-secondary/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            <div className="absolute top-0 right-0 w-32 h-32 bg-accent/10 rounded-full blur-3xl group-hover:bg-accent/20 transition-all" />
            <div className="relative p-8 space-y-6">
              <div className="flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-br from-accent to-secondary group-hover:scale-110 transition-transform shadow-lg">
                <Users className="w-10 h-10 text-accent-foreground" />
              </div>
              <div className="space-y-3">
                <h2 className="text-3xl font-display text-foreground tracking-wide">
                  TILT MASTER!
                </h2>
                <p className="text-foreground/80 leading-relaxed text-lg font-semibold">
                  Become a tilting LEGEND! Wobble your head like a pro and master the ultimate tilt challenge!
                </p>
              </div>
              <Button
                onClick={() => {
                  launchGame(1)
                  setActiveGame(1)
                }}
                disabled={loading !== null}
                className="w-full h-16 text-2xl font-display tracking-wider bg-gradient-to-r from-accent via-secondary to-accent hover:scale-105 active:scale-95 transition-all shadow-xl hover:shadow-2xl disabled:opacity-50"
                size="lg"
              >
                {loading === 1 ? (
                  <span className="flex items-center gap-3">
                    <span className="w-6 h-6 border-4 border-accent-foreground/30 border-t-accent-foreground rounded-full animate-spin" />
                    STARTING...
                  </span>
                ) : (
                  'PLAY NOW!'
                )}
              </Button>
            </div>
          </Card>
        </div>

        <div className="text-center text-lg font-bold text-muted-foreground animate-pulse">
          <p>Make sure neazbackend is running on port 2301!</p>
        </div>
      </div>
    </div>
  )
}