'use client'

import { useEffect, useState } from 'react'

interface SillyTilterProps {
  onHover?: () => void
  gameHovered?: number | null
  gameLoading?: number | null
  activeGame?: number | null
}

export function SillyTilter({ onHover, gameHovered, gameLoading, activeGame }: SillyTilterProps) {
  const [tilt, setTilt] = useState(0)
  const [message, setMessage] = useState('Heyooo! Welcome to the Game Hub!')
  const [eyePosition, setEyePosition] = useState({ x: 0, y: 0 })
  const [bounceAmount, setBounceAmount] = useState(0)
  const [expression, setExpression] = useState<'happy' | 'excited' | 'super-excited'>('happy')
  const [isWelcomePhase, setIsWelcomePhase] = useState(true)
  const [waveAnimation, setWaveAnimation] = useState(0)

  const welcomeMessages = [
    'HEYYYY THERE! Welcome to Game Hub!',
    '*waves excitedly* SO GLAD YOU\'RE HERE!',
    'Hi hi hi! I\'m SillyTilter! Nice to meet you!',
    '*tilts head and waves* Let\'s play some GAMES!',
  ]

  const idleMessages = [
    'Heyooo! Welcome to the Game Hub!',
    'Ooh, pick me! I mean... pick a game!',
    'I\'m kinda tilted about these games... they\'re AWESOME!',
    'Psst! Both games are super duper fun!',
    'My head goes wobbly when I\'m excited!',
    'Did someone say GAMES?! *tilts enthusiastically*',
  ]

  const hoverMessages = {
    0: [
      'Ooh! Traffic game! Watch out for those cars!',
      'This one\'s great for your posture... unlike my tilted head!',
      'Beep beep! Car sounds! Vrooom!',
    ],
    1: [
      'Head tilt challenge? I\'m an EXPERT at that!',
      'This game speaks my language... literally!',
      'Tilt your head like me! It\'s super fun!',
    ],
  }

  const loadingMessages = {
    0: [
      'Buckle up! Game is loading!',
      'Vroom vroom! Starting engines!',
      'Get ready to dodge traffic!',
    ],
    1: [
      'Tilting... tilting... GAME TIME!',
      'Let\'s get this head party started!',
      'Wobble wobble! Here we gooo!',
    ],
  }

  const tiltMasterMessages = [
    'WOOO! Tilt Master is AMAZING! *tilts wildly*',
    'I\'m tilting SO MUCH right now! Can you feel it?!',
    'This is MY game! Watch me go! *wobbles intensely*',
    'TILT TILT TILT! I can\'t stop! This is too fun!',
    'Look at me go! I\'m the KING of tilting!',
    'My neck is having the TIME OF ITS LIFE!',
  ]

  useEffect(() => {
    // Welcome phase lasts 8 seconds
    const welcomeTimer = setTimeout(() => {
      setIsWelcomePhase(false)
    }, 8000)

    let currentTilt = 0
    let direction = 1
    let messageIndex = 0
    let currentBounce = 0
    let bounceDirection = 1
    let waveCount = 0

    // Enhanced tilting for Tilt Master mode
    const isTiltMasterMode = activeGame === 1
    const isWelcome = isWelcomePhase
    const tiltSpeed = isTiltMasterMode ? 4.5 : isWelcome ? 3.5 : 2.5
    const tiltRange = isTiltMasterMode ? 35 : isWelcome ? 25 : 20
    const bounceSpeed = isTiltMasterMode ? 1.2 : isWelcome ? 0.8 : 0.5
    const bounceRange = isTiltMasterMode ? 10 : isWelcome ? 8 : 5

    if (isTiltMasterMode) {
      setExpression('super-excited')
    } else if (gameLoading !== null || gameHovered !== null || isWelcome) {
      setExpression('excited')
    } else {
      setExpression('happy')
    }

    // Wave animation for welcome phase
    const waveInterval = isWelcome ? setInterval(() => {
      waveCount += 1
      setWaveAnimation(Math.sin(waveCount * 0.3) * 20)
    }, 100) : null

    const tiltInterval = setInterval(() => {
      currentTilt += direction * tiltSpeed
      if (currentTilt >= tiltRange || currentTilt <= -tiltRange) {
        direction *= -1
      }
      setTilt(currentTilt)
    }, 40)

    const bounceInterval = setInterval(() => {
      currentBounce += bounceDirection * bounceSpeed
      if (currentBounce >= bounceRange || currentBounce <= 0) {
        bounceDirection *= -1
      }
      setBounceAmount(currentBounce)
    }, 50)

    const eyeInterval = setInterval(() => {
      const eyeSpeed = isTiltMasterMode ? 500 : 1000
      const eyeRange = isTiltMasterMode ? 4 : 2
      setEyePosition({
        x: Math.sin(Date.now() / eyeSpeed) * eyeRange,
        y: Math.cos(Date.now() / (eyeSpeed * 0.8)) * (eyeRange * 0.5),
      })
    }, 50)

    const messageInterval = setInterval(() => {
      if (isWelcome) {
        setMessage(welcomeMessages[Math.floor(Math.random() * welcomeMessages.length)])
      } else if (isTiltMasterMode) {
        setMessage(tiltMasterMessages[Math.floor(Math.random() * tiltMasterMessages.length)])
      } else if (gameLoading !== null) {
        const msgs = loadingMessages[gameLoading as keyof typeof loadingMessages]
        setMessage(msgs[Math.floor(Math.random() * msgs.length)])
      } else if (gameHovered !== null) {
        const msgs = hoverMessages[gameHovered as keyof typeof hoverMessages]
        setMessage(msgs[Math.floor(Math.random() * msgs.length)])
      } else {
        messageIndex = (messageIndex + 1) % idleMessages.length
        setMessage(idleMessages[messageIndex])
      }
    }, isWelcome ? 1500 : isTiltMasterMode ? 2000 : 3000)

    return () => {
      clearTimeout(welcomeTimer)
      clearInterval(tiltInterval)
      clearInterval(messageInterval)
      clearInterval(eyeInterval)
      clearInterval(bounceInterval)
      if (waveInterval) clearInterval(waveInterval)
    }
  }, [gameHovered, gameLoading, activeGame, isWelcomePhase])

  return (
    <div 
      className="flex flex-col items-center gap-6 cursor-pointer"
      style={{ transform: `translateY(-${bounceAmount}px)` }}
      onMouseEnter={onHover}
    >
      <div className="relative">
        {/* Robot Head */}
        <div
          className="relative transition-transform duration-75 ease-linear"
          style={{ transform: `rotate(${tilt}deg) scale(${gameLoading !== null ? 1.1 : 1})` }}
        >
          {/* Main head circle */}
          <div className="w-40 h-40 bg-gradient-to-br from-primary via-secondary to-accent rounded-[2rem] shadow-2xl relative border-4 border-primary-foreground/30 hover:border-primary-foreground/50 transition-all">
            {/* Antenna */}
            <div className="absolute -top-10 left-1/2 -translate-x-1/2 w-1.5 h-10 bg-gradient-to-t from-primary to-accent rounded-full">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-4 h-4 bg-accent rounded-full animate-pulse shadow-lg shadow-accent/50" />
            </div>

            {/* Eyes - change size based on expression */}
            <div 
              className={`absolute top-10 left-8 bg-background rounded-full flex items-center justify-center shadow-inner transition-all ${
                expression === 'super-excited' ? 'w-10 h-10' : 'w-8 h-8'
              }`}
              style={{ transform: `translate(${eyePosition.x}px, ${eyePosition.y}px)` }}
            >
              <div className={`bg-foreground rounded-full animate-pulse ${
                expression === 'super-excited' ? 'w-5 h-5' : 'w-4 h-4'
              }`} />
            </div>
            <div 
              className={`absolute top-10 right-8 bg-background rounded-full flex items-center justify-center shadow-inner transition-all ${
                expression === 'super-excited' ? 'w-10 h-10' : 'w-8 h-8'
              }`}
              style={{ transform: `translate(${eyePosition.x}px, ${eyePosition.y}px)` }}
            >
              <div className={`bg-foreground rounded-full animate-pulse ${
                expression === 'super-excited' ? 'w-5 h-5' : 'w-4 h-4'
              }`} />
            </div>

            {/* Smile - changes based on state */}
            <div className={`absolute bottom-8 left-1/2 -translate-x-1/2 border-b-[5px] border-background rounded-full transition-all ${
              expression === 'super-excited' ? 'w-20 h-10 scale-125 border-b-[6px]' : 
              expression === 'excited' ? 'w-16 h-8 scale-110' : 'w-16 h-8'
            }`} />
            
            {/* Cheeks - bigger and more colorful when excited */}
            <div className={`absolute bottom-12 left-4 rounded-full transition-all ${
              expression === 'super-excited' ? 'w-6 h-6 bg-accent/60 animate-pulse' : 'w-4 h-4 bg-accent/40 animate-pulse'
            }`} />
            <div className={`absolute bottom-12 right-4 rounded-full transition-all ${
              expression === 'super-excited' ? 'w-6 h-6 bg-accent/60 animate-pulse' : 'w-4 h-4 bg-accent/40 animate-pulse'
            }`} />
          </div>
        </div>

        {/* Robot Body - doesn't tilt */}
        <div className="w-28 h-20 bg-gradient-to-b from-primary/90 to-primary/70 rounded-3xl mx-auto mt-3 border-4 border-primary-foreground/20 shadow-xl">
          <div className="flex justify-center gap-2 mt-3">
            <div className="w-3 h-3 bg-accent rounded-full animate-pulse shadow-lg shadow-accent/50" />
            <div className="w-3 h-3 bg-secondary rounded-full animate-pulse delay-75 shadow-lg shadow-secondary/50" />
            <div className="w-3 h-3 bg-accent rounded-full animate-pulse delay-150 shadow-lg shadow-accent/50" />
          </div>
          {/* Arms */}
          <div 
            className="absolute top-32 -left-6 w-6 h-12 bg-primary rounded-full border-2 border-primary-foreground/20 transition-transform duration-100"
            style={{ transform: `rotate(${12 + (isWelcomePhase ? waveAnimation : 0)}deg)` }}
          />
          <div className="absolute top-32 -right-6 w-6 h-12 bg-primary rounded-full -rotate-12 border-2 border-primary-foreground/20" />
        </div>
      </div>

      {/* Message bubble */}
      <div className="relative bg-gradient-to-br from-card to-card/80 border-3 border-primary/30 rounded-3xl px-8 py-5 shadow-2xl shadow-primary/20 max-w-md backdrop-blur-sm">
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-6 h-6 bg-gradient-to-br from-card to-card/80 border-t-3 border-l-3 border-primary/30 rotate-45" />
        <p className="text-center text-foreground font-bold text-lg text-balance leading-relaxed">
          {message}
        </p>
      </div>
    </div>
  )
}
