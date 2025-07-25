import agentsConfig from '../assets/agents.json'

function Agent({mode}) {

    const agentsToDisplay = ( mode === 'personal' ? agentsConfig.personal : agentsConfig.work );

    return (
        <div className="agents-panel">
            {agentsToDisplay.map(agent => (
                <div className="agent-card" key={agent.id}>
                    <div className="agent-header">
                        <div className="agent-icon">{agent.icon}</div>
                        <div>
                            <div className="agent-name">{agent.name}</div>
                            <div className="agent-status status-idle" id="status${agent.id}">{agent.status}</div>
                        </div>
                    </div>
                    <div className="agent-description">
                        {agent.description}
                    </div>
                </div>
            ))}
        </div>
    )
}

export default Agent;