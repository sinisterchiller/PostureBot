import type { Metadata } from 'next'
import { Bangers, Comic_Neue } from 'next/font/google'
import { ToasterWrapper } from '@/components/toaster-wrapper'

import './globals.css'

const bangers = Bangers({ 
  weight: '400',
  subsets: ['latin'],
  variable: '--font-bangers'
})

const comicNeue = Comic_Neue({ 
  weight: ['300', '400', '700'],
  subsets: ['latin'],
  variable: '--font-comic'
})

export const metadata: Metadata = {
  title: 'Game Hub - Interactive Game Launcher',
  description: 'Choose between Traffic & Posture Game or Head Tilt Challenge. Featuring SillyTilter, your friendly AI assistant!',
  generator: 'v0.app',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`${bangers.variable} ${comicNeue.variable}`}>
      <body className="font-sans antialiased">
        {children}
        <ToasterWrapper />
      </body>
    </html>
  )
}
