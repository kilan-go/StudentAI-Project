import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, FlatList, TouchableOpacity, Alert, ActivityIndicator, SafeAreaView } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import { useStore } from '../src/store/store';

// CHANGE THIS TO YOUR PYTHON SERVER URL
const API_URL = 'https://studentai-yl16.onrender.com'; // Example

export default function ChatScreen() {
    const { profile, isGuest, user, signOut } = useStore();
    const [messages, setMessages] = useState<{ role: string, content: string }[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [usageCount, setUsageCount] = useState(0);

    useEffect(() => {
        if (isGuest && usageCount > 0 && usageCount % 5 === 0) {
            Alert.alert("Upgrade", "Register to save history and upload more files!");
        }
    }, [usageCount]);

    const handleUpload = async () => {
        if (isGuest) return Alert.alert("Restricted", "Guests cannot upload files.");

        const result = await DocumentPicker.getDocumentAsync({ type: 'text/plain' });
        if (result.canceled) return;

        setLoading(true);
        const file = result.assets[0];

        // Create Form Data for Python Backend
        const formData = new FormData();
        formData.append('file', {
            uri: file.uri,
            name: file.name,
            type: file.mimeType || 'text/plain',
        } as any);
        formData.append('user_id', user.id);

        try {
            const res = await fetch(`${API_URL}/upload`, {
                method: 'POST',
                body: formData,
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            if (res.ok) Alert.alert("Success", "Document added to brain.");
            else Alert.alert("Error", "Upload failed");
        } catch (e) {
            Alert.alert("Error", "Server unreachable");
        }
        setLoading(false);
    };

    const sendMessage = async () => {
        if (!input.trim()) return;

        const userMsg = input;
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setInput('');
        setLoading(true);
        setUsageCount(c => c + 1);

        try {
            const res = await fetch(`${API_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: isGuest ? null : user.id,
                    query: userMsg,
                    role: profile?.role || 'student',
                    course: profile?.course || 'General',
                    level: profile?.level || 'Basic'
                })
            });

            const data = await res.json();
            setMessages(prev => [...prev, { role: 'ai', content: data.answer }]);
        } catch (e) {
            setMessages(prev => [...prev, { role: 'ai', content: "Error: Could not connect to AI server." }]);
        }
        setLoading(false);
    };

    return (
        <SafeAreaView className="flex-1 bg-gray-50 dark:bg-black">
            <View className="p-4 border-b border-gray-200 flex-row justify-between items-center bg-white">
                <Text className="text-xl font-bold text-blue-600">Student AI</Text>
                {!isGuest && <TouchableOpacity onPress={signOut}><Text className="text-red-500">Log out</Text></TouchableOpacity>}
            </View>

            <FlatList
                data={messages}
                keyExtractor={(_, i) => i.toString()}
                renderItem={({ item }) => (
                    <View className={`p-3 m-2 rounded-xl max-w-[80%] ${item.role === 'user' ? 'bg-blue-600 self-end' : 'bg-gray-200 self-start'}`}>
                        <Text className={item.role === 'user' ? 'text-white' : 'text-black'}>{item.content}</Text>
                    </View>
                )}
            />

            {loading && <ActivityIndicator size="small" color="#2563eb" />}

            <View className="flex-row items-center p-4 bg-white">
                <TouchableOpacity onPress={handleUpload} className="mr-3"><Text className="text-2xl">📎</Text></TouchableOpacity>
                <TextInput value={input} onChangeText={setInput} placeholder="Ask..." className="flex-1 bg-gray-100 p-3 rounded-full" />
                <TouchableOpacity onPress={sendMessage} className="ml-3 bg-blue-600 p-3 rounded-full"><Text className="text-white font-bold">Send</Text></TouchableOpacity>
            </View>
        </SafeAreaView>
    );
}