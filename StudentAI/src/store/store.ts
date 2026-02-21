import { create } from 'zustand';
import { supabase } from '../lib/supabase';

interface AppState {
    user: any | null;
    profile: any | null;
    isGuest: boolean;
    signIn: (session: any) => Promise<void>;
    setGuest: () => void;
    signOut: () => Promise<void>;
}

export const useStore = create<AppState>((set) => ({
    user: null,
    profile: null,
    isGuest: false,
    signIn: async (session) => {
        const { data } = await supabase.from('profiles').select('*').eq('id', session.user.id).single();
        set({ user: session.user, profile: data, isGuest: false });
    },
    setGuest: () => set({ isGuest: true, user: { id: 'guest' }, profile: null }),
    signOut: async () => {
        await supabase.auth.signOut();
        set({ user: null, profile: null, isGuest: false });
    },
}));