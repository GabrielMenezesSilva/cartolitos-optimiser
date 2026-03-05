import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
    apiKey: "AIzaSyBulGp5euEBVMgUgXOLjVjJIRSeQsNrbDE",
    authDomain: "cartolitos-optimiser.firebaseapp.com",
    projectId: "cartolitos-optimiser",
    storageBucket: "cartolitos-optimiser.firebasestorage.app",
    messagingSenderId: "69188912827",
    appId: "1:69188912827:web:e6008e037e0d2f19350b9e"
};

const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const db = getFirestore(app);
export const googleProvider = new GoogleAuthProvider();

export const loginWithGoogle = () => signInWithPopup(auth, googleProvider);
export const logout = () => signOut(auth);
