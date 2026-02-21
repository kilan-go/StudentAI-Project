import { Stack, useRouter, useSegments } from 'expo-router';
import { useEffect, useState } from 'react';
import { useStore } from '../src/store/store';
import { View, ActivityIndicator } from 'react-native';
import { supabase } from '../src/lib/supabase';

export default function RootLayout() {
    const { user, profile, isGuest, signIn } = useStore();
    const segments = useSegments();
    const router = useRouter();
    const [loading, setLoading] = useState(true);

    // Check for existing session on app start
    useEffect(() => {
        supabase.auth.getSession().then(({ data: { session } }) => {
            if (session) signIn(session);
            setLoading(false);
        });
    }, []);

    // Auth Guard Logic
    useEffect(() => {
        if (loading) return;

        const inAuthGroup = segments[0] === 'auth';

        if (!user && !isGuest && !inAuthGroup) {
            router.replace('/auth'); // Go to Login
        } else if (user && !profile && !isGuest && segments[0] !== 'onboarding') {
            router.replace('/onboarding'); // Go to Profile Setup
        } else if ((user || isGuest) && inAuthGroup) {
            router.replace('/'); // Go to Chat
        }
    }, [user, profile, isGuest, segments, loading]);

    if (loading) return <View className="flex-1 bg-white justify-center"><ActivityIndicator /></View>;

    return (
        <Stack screenOptions={{ headerShown: false }}>
            <Stack.Screen name="index" />
            <Stack.Screen name="auth" />
            <Stack.Screen name="onboarding" />
        </Stack>
    );
}