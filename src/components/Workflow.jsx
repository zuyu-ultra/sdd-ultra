import { useState } from 'react'
import { workflowStages } from '../data.js'
import { ArrowRight, FileIcon } from './Icons.jsx'

export default function Workflow() {
  const [activeId, setActiveId] = useState('specify')
  const active = workflowStages.find((stage) => stage.id === activeId)

  return (
    <section className="workflow-section" id="workflow">
      <div className="section-inner">
        <div className="workflow-heading bracket-frame">
          <h2>SDD 不是多写文档，<br />而是建立一条可验证的链路</h2>
          <p>每一步都产生明确产物，也为下一步缩小决策空间。</p>
        </div>
        <div className="stage-rail" role="tablist" aria-label="SDD 工作流阶段">
          {workflowStages.map((stage) => (
            <button
              key={stage.id}
              className={stage.id === activeId ? 'stage-tab is-active' : 'stage-tab'}
              onClick={() => setActiveId(stage.id)}
              role="tab"
              aria-selected={stage.id === activeId}
            >
              <span>{stage.number}</span><strong>{stage.short}</strong><i />
            </button>
          ))}
        </div>
        <div className="stage-detail" role="tabpanel" key={active.id}>
          <div className="stage-copy">
            <div className="stage-title"><span>{active.number}</span><h3>{active.short}</h3></div>
            <h4>{active.title}</h4>
            <p>{active.description}</p>
            <div className="file-link"><FileIcon size={25} /><code>{active.file}</code><ArrowRight size={20} /></div>
          </div>
          <div className="document-preview">
            <div className="document-head"><code>{active.file}</code><span>VERSION 0.1.0</span></div>
            {active.sample.map(([key, value]) => (
              <div className="document-line" key={key}><strong>{key}</strong><span>{value}</span></div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
