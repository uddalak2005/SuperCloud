export interface PolicyDecision {
    allowed: boolean;
    reason?: string;
}

export function evaluatePolicy(action: string, severity : string) : PolicyDecision {
    if(action == "DELETE_RESOURCE") {
        return {
            allowed: false,
            reason: "Destructive Action Needs Human Intervention",
        }
    }

    if(severity == "LOW" && action == "SCALE_SERVICE") {
        return {
            allowed: false,
            reason: "Auto-scaling not allowed for LOW severity incidents"
        }
    }

    return{
        allowed: true,
    }
}
