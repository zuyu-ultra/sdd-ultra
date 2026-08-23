import { useState } from 'react'

const promptOnly = ['上下文容易丢失', '决策无法追踪', '验收依赖感觉']
const sdd = ['目标写入规格', '决策留在计划', '验收对应成功标准']

export default function Comparison() {
  const [focus, setFocus] = useState('sdd')
  return (
    <section className="comparison-section" id="what">
      <div className="section-inner">
        <div className="section-heading compact-heading">
          <span>对比视图</span>
          <h2>从模糊对话，<br />到可追踪的工程事实</h2>
          <p>点击切换，看看一次对话和一条工程链路的差别。</p>
        </div>
        <div className="comparison-board">
          <button className={focus === 'prompt' ? 'comparison-col is-focused' : 'comparison-col'} onClick={() => setFocus('prompt')}>
            <span className="comparison-label">只写 Prompt</span>
            {promptOnly.map((item) => <span className="comparison-item negative" key={item}><b>×</b>{item}</span>)}
          </button>
          <button className="comparison-switch" aria-label="切换对比重点" onClick={() => setFocus(focus === 'sdd' ? 'prompt' : 'sdd')}>
            <span className={focus === 'sdd' ? 'switch-track is-right' : 'switch-track'}><i /></span>
            <small>{focus === 'sdd' ? '聚焦 SDD' : '聚焦 Prompt'}</small>
          </button>
          <button className={focus === 'sdd' ? 'comparison-col sdd-col is-focused' : 'comparison-col sdd-col'} onClick={() => setFocus('sdd')}>
            <span className="comparison-label">使用 SDD</span>
            {sdd.map((item) => <span className="comparison-item positive" key={item}><b>✓</b>{item}</span>)}
          </button>
        </div>
      </div>
    </section>
  )
}
