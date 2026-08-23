import { ArrowRight } from './Icons.jsx'

const flow = [
  ['01', '意图', '用户真正要解决的问题'],
  ['02', '规格', '需求、边界与成功标准'],
  ['03', '计划', '方案、任务与风险'],
  ['04', '代码', '实现、验证与收敛'],
]

export default function BlueprintFlow() {
  return (
    <div className="blueprint" aria-label="从意图到代码的 SDD 流程图">
      <div className="blueprint-top"><span>SDD FLOW</span><span>SPEC-FIRST, AI-ALIGNED</span></div>
      <div className="flow-row">
        {flow.map(([number, title, body], index) => (
          <div className="flow-unit" key={number}>
            <div className="flow-card">
              <span className="flow-number">{number}</span>
              <strong>{title}</strong>
              <div className="flow-code"><span /> <span /> <span /></div>
              <p>{body}</p>
            </div>
            {index < flow.length - 1 && <span className="flow-arrow"><ArrowRight size={25} /></span>}
          </div>
        ))}
      </div>
      <div className="feedback-loop"><span>发现偏差，回到规格修正</span></div>
      <div className="blueprint-bottom"><span>v1.0</span><span>SDD = Specification-Driven Development</span></div>
    </div>
  )
}
