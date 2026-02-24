export interface ExecutionResult {
    success: boolean;
    message: string;
}

export const executeAction = async (
    action: string,
    service: string
): Promise<ExecutionResult> => {
    // Simulation mode
    switch (action) {
        case "SCALE_SERVICE":
            return {
                success: true,
                message: `Scaled ${service} replicas from 2 → 4`,
            };

        case "RESTART_POD":
            return {
                success: true,
                message: `Restarted pods for ${service}`,
            };

        default:
            return {
                success: false,
                message: "Unknown remediation action",
            };
    }
};