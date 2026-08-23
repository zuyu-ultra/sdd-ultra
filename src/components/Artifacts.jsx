import { artifacts } from '../data.js'
import { FileIcon } from './Icons.jsx'

export default function Artifacts() {
  return (
    <section className="artifacts-section" id="artifacts">
      <div className="section-inner">
        <div className="artifact-heading"><h2>一条功能链，六类关键产物</h2><p>不是为了留档，而是为了让意图、决策和验收都有明确的落点。</p></div>
        <div className="artifact-rail">
          {artifacts.map(([number, file, title, description]) => (
            <div className="artifact" key={file}>
              <span className="artifact-number">{number}</span>
              <FileIcon />
              <code>{file}</code>
              <strong>{title}</strong>
              <p>{description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
