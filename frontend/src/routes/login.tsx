import { createFileRoute } from '@tanstack/react-router'
import { LoginPage } from '#/features/auth/LoginPage'
import { requireGuest } from '#/lib/route-guards'

export const Route = createFileRoute('/login')({
  beforeLoad: requireGuest,
  component: LoginPage,
})
