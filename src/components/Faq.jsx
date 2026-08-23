import { useState } from 'react'
import { faqs } from '../data.js'
import { PlusIcon } from './Icons.jsx'

export default function Faq() {
  const [openIndex, setOpenIndex] = useState(0)
  return (
    <section className="faq-section" id="faq">
      <div className="section-inner faq-layout">
        <div className="faq-title bracket-frame"><h2>常见问题</h2><p>把常见误解先说清楚。</p></div>
        <div className="faq-list">
          {faqs.map((faq, index) => {
            const open = openIndex === index
            return (
              <div className={open ? 'faq-item is-open' : 'faq-item'} key={faq.question}>
                <button onClick={() => setOpenIndex(open ? -1 : index)} aria-expanded={open}>
                  <span>{faq.question}</span><PlusIcon open={open} />
                </button>
                <div className="faq-answer"><p>{faq.answer}</p></div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
