import React, { createContext, useContext, useEffect, useState } from 'react'
import {
  User,
  onAuthStateChanged,
  signInAnonymously,
  signInWithPopup,
  signOut as firebaseSignOut,
  GoogleAuthProvider,
  GithubAuthProvider,
  TwitterAuthProvider,
  FacebookAuthProvider,
  AuthError
} from 'firebase/auth'
import { auth } from '../firebase'

interface AuthContextType {
  user: User | null
  loading: boolean
  signInWithGoogle: () => Promise<void>
  signInWithGithub: () => Promise<void>
  signInWithTwitter: () => Promise<void>
  signInWithFacebook: () => Promise<void>
  signOut: () => Promise<void>
  authError: string | null
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [authError, setAuthError] = useState<string | null>(null)

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (u) => {
      if (u) {
        setUser(u)
        setLoading(false)
      } else {
        // Auto sign in anonymously when no user
        try {
          await signInAnonymously(auth)
        } catch (_err) {
          setAuthError('Failed to initialize session')
          setLoading(false)
        }
      }
    })
    return unsubscribe
  }, [])

  const handlePopupSignIn = async (
    provider:
      | GoogleAuthProvider
      | GithubAuthProvider
      | TwitterAuthProvider
      | FacebookAuthProvider
  ) => {
    setAuthError(null)
    try {
      await signInWithPopup(auth, provider)
    } catch (err) {
      const error = err as AuthError
      setAuthError(error.message)
    }
  }

  const signInWithGoogle = () => handlePopupSignIn(new GoogleAuthProvider())
  const signInWithGithub = () => handlePopupSignIn(new GithubAuthProvider())
  const signInWithTwitter = () => handlePopupSignIn(new TwitterAuthProvider())
  const signInWithFacebook = () => handlePopupSignIn(new FacebookAuthProvider())

  const signOut = async () => {
    await firebaseSignOut(auth)
    // onAuthStateChanged will trigger anonymous sign-in
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        signInWithGoogle,
        signInWithGithub,
        signInWithTwitter,
        signInWithFacebook,
        signOut,
        authError,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
