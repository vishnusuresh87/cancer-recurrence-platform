import React from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from 'recharts';

interface Props {
    data: Array<{
        months: number;
        years: number;
        recurrence_probability_pct: number;
    }>;
}

export const SurvivalCurveChart: React.FC<Props> = ({ data }) => {
    return (
        <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                    dataKey="years"
                    label={{ value: 'Years Since Diagnosis', position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                    label={{ value: 'Recurrence Probability (%)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip
                    formatter={(value: number) => `${value.toFixed(1)}%`}
                    labelFormatter={(label) => `${label} years`}
                />
                <Legend />
                <Line
                    type="monotone"
                    dataKey="recurrence_probability_pct"
                    stroke="#8884d8"
                    strokeWidth={2}
                    name="Recurrence Probability"
                />
            </LineChart>
        </ResponsiveContainer>
    );
};

