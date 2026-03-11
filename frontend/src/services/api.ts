import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

// Interceptor to attach the token
api.interceptors.request.use((config: any) => {
    // We can't synchronously get the token from Context here easily without hooks,
    // so we'll pass the token directly to the functions that need it.
    return config;
});

export const fetchLineupHistory = async (token: string) => {
    const response = await api.get('/api/v1/history/audit', {
        headers: {
            Authorization: `Bearer ${token}`
        }
    });
    return response.data;
};

export const saveLineup = async (token: string, roundId: number, expectedPoints: number, cost: number, lineup: any, strategy: string) => {
    const response = await api.post('/api/v1/history/save', {
        round_id: roundId,
        expected_points: expectedPoints,
        cost: cost,
        lineup_data: lineup,
        strategy: strategy
    }, {
        headers: {
            Authorization: `Bearer ${token}`
        }
    });

    return response.data;
}

export const optimizeLineup = async (budget: number, modo: string, token: string | null = null) => {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const response = await api.get('/api/v1/cartola/optimize-real', {
        params: {
            budget,
            modo,
            formation: '4-3-3'
        },
        headers
    });
    return response.data;
};

export const optimizeMultiple = async (budget: number, modo: string, token: string | null = null, numLineups = 3) => {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const response = await api.get('/api/v1/cartola/optimize-real/multiple', {
        params: {
            budget,
            modo,
            formation: '4-3-3',
            num_lineups: numLineups,
        },
        headers
    });
    return response.data; // { lineups: [...], total: N }
};

export default api;
