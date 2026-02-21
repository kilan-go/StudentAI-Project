import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, Alert } from 'react-native';
import { useStore } from '../src/store/store';
import { supabase } from '../src/lib/supabase';

export default function AuthScreen() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLogin, setIsLogin] = useState(true);
    const { signIn, setGuest } = useStore();

    const handleAuth = async () => {
        try {
            if (isLogin) {
                const { data, error } = await supabase.auth.signInWithPassword({ email, password });
                if (error) throw error;
                await signIn(data.session);
            } else {
                const { error } = await supabase.auth.signUp({ email, password });
                if (error) throw error;
                Alert.alert("Success", "Registration successful! Please login.");
                setIsLogin(true);
            }
        } catch (e: any) {
            Alert.alert("Error", e.message);
        }
    };

    return (
        <View className="flex-1 justify-center p-6 bg-gray-100 dark:bg-gray-900">
            <Text className="text-3xl font-bold text-blue-600 mb-8 text-center">Student AI</Text>

            <TextInput placeholder="Email" value={email} onChangeText={setEmail} className="bg-white p-4 rounded-xl mb-3" autoCapitalize="none" />
            <TextInput placeholder="Password" value={password} onChangeText={setPassword} secureTextEntry className="bg-white p-4 rounded-xl mb-6" />

            <TouchableOpacity onPress={handleAuth} className="bg-blue-600 p-4 rounded-xl items-center">
                <Text className="text-white font-bold">{isLogin ? "Login" : "Register"}</Text>
            </TouchableOpacity>

            <TouchableOpacity onPress={() => setIsLogin(!isLogin)} className="mt-4 items-center">
                <Text className="text-blue-500">{isLogin ? "Create account" : "Have an account?"}</Text>
            </TouchableOpacity>

            <TouchableOpacity onPress={setGuest} className="mt-8 items-center">
                <Text className="text-gray-500 underline">Continue as Guest</Text>
            </TouchableOpacity>
        </View>
    );
}