import { useAuth } from '../contexts/AuthContext'

export function AuthPanel() {
  const {
    user,
    signInWithGoogle,
    signInWithGithub,
    signInWithTwitter,
    signInWithFacebook,
    signOut,
    authError,
  } = useAuth()

  const isAnonymous = user?.isAnonymous ?? true

  return (
    <div className="flex items-center gap-2">
      {authError && <span className="text-red-500 text-sm">{authError}</span>}
      {isAnonymous ? (
        <div className="flex gap-2">
          <button
            onClick={signInWithGoogle}
            className="px-3 py-1 text-sm bg-white border rounded hover:bg-gray-50"
          >
            Google
          </button>
          <button
            onClick={signInWithGithub}
            className="px-3 py-1 text-sm bg-white border rounded hover:bg-gray-50"
          >
            GitHub
          </button>
          <button
            onClick={signInWithTwitter}
            className="px-3 py-1 text-sm bg-white border rounded hover:bg-gray-50"
          >
            Twitter
          </button>
          <button
            onClick={signInWithFacebook}
            className="px-3 py-1 text-sm bg-white border rounded hover:bg-gray-50"
          >
            Facebook
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">
            {user?.displayName ?? user?.email ?? 'User'}
          </span>
          <button
            onClick={signOut}
            className="px-3 py-1 text-sm bg-white border rounded hover:bg-gray-50"
          >
            Sign out
          </button>
        </div>
      )}
    </div>
  )
}
