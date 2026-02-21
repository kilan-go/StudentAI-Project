import React, { useState } from 'react';
import { View, Text, TouchableOpacity, TextInput } from 'react-native';
import { useRouter } from 'expo-router';
import { useStore } from '../src/store/store';
import { supabase } from '../src/lib/supabase';

export default function OnboardingScreen() {
    const { user, signIn } = useStore();
    const router = useRouter();
    const [role, setRole] = useState('student');
    const [course, setCourse] = useState('Computer Science');
    const [level, setLevel] = useState('Bachelor');

    const saveProfile = async () => {
        // 1. Save to DB
        await supabase.from('profiles').upsert({
            id: user.id,
            role, course, level, is_guest: false
        });

        // 2. Refresh local session to update state in _layout
        const { data } = await supabase.auth.refreshSession();
        if (data.session) await signIn(data.session);

        // 3. Router will auto-redirect in _layout
    };

    return (
        <View className="flex-1 p-6 bg-white pt-20">
            <Text className="text-2xl font-bold mb-6">Setup Profile</Text>

            <Text className="mb-2">Role:</Text>
            <View className="flex-row mb-4">
                {['student', 'teacher'].map(r => (
                    <TouchableOpacity key={r} onPress={() => setRole(r)} className={`p-3 mr-2 border rounded ${role === r ? 'bg-blue-100 border-blue-500' : 'border-gray-200'}`}>
                        <Text className="capitalize">{r}</Text>
                    </TouchableOpacity>
                ))}
            </View>

            <Text className="mb-2">Course:</Text>
            <TextInput value={course} onChangeText={setCourse} className="border border-gray-300 p-3 rounded-lg mb-4" />

            <Text className="mb-2">Level:</Text>
            <TextInput value={level} onChangeText={setLevel} className="border border-gray-300 p-3 rounded-lg mb-8" />

            <TouchableOpacity onPress={saveProfile} className="bg-blue-600 p-4 rounded-xl">
                <Text className="text-white text-center font-bold">Start</Text>
            </TouchableOpacity>
        </View>
    );
}