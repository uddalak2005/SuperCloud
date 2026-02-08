import axios from "axios";
import {AGENT_REGISTRY} from "./agents.registry";

export interface AgentResponse {
    decision : string;
    confidence : number;
    explanation? : string;
};


export async function callAgent(
    agentName : keyof typeof AGENT_REGISTRY,
    payload : any,
) : Promise<AgentResponse> {


        if(! AGENT_REGISTRY[agentName]){
            throw new Error(`${agentName} doesn't exist`);
        }

        // ---- MOCK MODE (for now) ----
        return {
            decision: "SCALE_SERVICE",
            confidence: 0.91,
            explanation: "High CPU usage detected across replicas",
        };

        // ---- REAL MODE (later) ----
        /*
        const response = await axios.post(
          AGENT_REGISTRY[agentName].url,
          payload
        );
        return response.data;
        */

}