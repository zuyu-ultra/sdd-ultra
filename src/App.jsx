import Header from './components/Header.jsx'
import BlueprintFlow from './components/BlueprintFlow.jsx'
import Workflow from './components/Workflow.jsx'
import Comparison from './components/Comparison.jsx'
import Artifacts from './components/Artifacts.jsx'
import Faq from './components/Faq.jsx'
import { ArrowRight } from './components/Icons.jsx'

function Hero() {
  return (
    <main id="top">
      <section className="hero section-inner">
        <div className="hero-copy bracket-frame">
          <h1>用规格，<br />让 AI 开发可控</h1>
          <p>先把意图写成可验证的规格，<br />再让计划、任务与代码逐层对齐。</p>
          <div className="hero-actions">
            <a className="primary-button" href="#what">开始了解 <ArrowRight /></a>
            <a className="text-link" href="#workflow">查看完整流程 <ArrowRight /></a>
          </div>
        </div>
        <BlueprintFlow />
      </section>
      <section className="prompt-problem">
        <div className="section-inner prompt-row">
          <span className="section-index">01</span>
          <h2>为什么只写 Prompt 不够？</h2>
          <p>自然语言对话容易产生歧义、缺乏约束，也难以成为多人协作时长期有效的工程事实。</p>
          <a href="#what" aria-label="查看对比"><ArrowRight size={28} /></a>
        </div>
      </section>
    </main>
  )
}

function Closing() {
  return (
    <section className="closing-section">
      <div className="section-inner closing-band">
        <h2>从一份清晰的规格开始</h2>
        <a href="#workflow">查看 SDD 工作流 <ArrowRight /></a>
        <div className="closing-drawing" aria-hidden="true"><span /><span /><span /></div>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="section-inner site-footer">
      <div className="brand"><strong>SDD</strong><span>/</span><span>规格驱动开发</span></div>
      <p>让意图、决策与实现保持一致。</p>
    </footer>
  )
}

export default function App() {
  return (
    <>
      <Header />
      <Hero />
      <Comparison />
      <Workflow />
      <Artifacts />
      <Faq />
      <Closing />
      <Footer />
    </>
  )
}
