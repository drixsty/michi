/**
 * Homepage
 * Redirige automatiquement vers /dashboard
 */
import { redirect } from 'next/navigation';

export default function Home() {
  redirect('/dashboard');
}
