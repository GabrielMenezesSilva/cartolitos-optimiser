import { createClient } from '@supabase/supabase-js';

// URL and Publishable Key provided by the user
const supabaseUrl = 'https://vnufdzfedzncdiyxujgp.supabase.co';
const supabaseAnonKey = 'sb_publishable_qL4gq2cbnLCAZuWjvyVFKw__BsLsXcd';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export const loginWithGoogle = async () => {
    const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
            redirectTo: window.location.origin
        }
    });
    if (error) {
        console.error("Login attempt failed: ", error);
        throw error;
    }
    return data;
};

export const logout = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
};
