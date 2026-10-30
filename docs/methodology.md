# Source-backed selection and writing

## What is implemented

Reports are preserved in full in the private library. The generator retrieves report chunks with lexical TF-IDF cosine relevance and maximal marginal relevance (MMR), retaining all project identities and atomic facts. MMR balances query relevance with redundancy against already selected chunks. Its default lambda (0.7) is an engineering default, not a measured optimum. No embeddings, learned recruiter model, ATS simulation, or calibrated job-match percentage is claimed.

The final project choice still belongs to the language model. Retrieved scores rank report excerpts, not applicants or final project combinations. The private retrieval audit records chunk IDs, scores and source reports. Schema checks restrict project and evidence IDs; numeric checks and source qualifications provide additional mechanical controls, not semantic proof.

Writing follows Yale's Action–Project–Result and accomplishment/measurement/method formulations. Prefer specific personal actions and results with their baseline, unit and scope. Data volume is scope, not necessarily an improvement. Failed or inconclusive experiments can demonstrate diagnosis and decision quality without being rewritten as successful gains.

User-confirmed personal research ownership can guide active wording. It does not establish first authorship, accepted publication status, ownership of external frameworks, or production business outcomes.

## Sources and their limits

- Yale Office of Career Strategy: [Writing Impactful Resume Bullets](https://ocs.yale.edu/resources/writing-impactful-resume-bullets/). Career-writing guidance, not evidence of a guaranteed hiring lift.
- MIT CAPD: [Resumes: Writing about your skills](https://capd.mit.edu/resources/resumes-writing-about-your-skills/). PAR framing. Website fetch was rate limited during this review; the search-provided official excerpt was used as corroboration, not sole implementation guidance.
- Goldstein / Carbonell: [Using MMR for Diversity-Based Reranking](https://students.lti.cs.cmu.edu/11899/files/Final-p181-goldstein.pdf). Classic information retrieval and summarization method, adapted here to evidence retrieval. It has not been validated here as an optimum resume selector.
- Abhinav (2026): [Career-Aware Resume Tailoring via Multi-Source RAG with Provenance Tracking](https://arxiv.org/abs/2605.05257). A relevant recent case study: one candidate, nine job descriptions, proxy fit scores. It motivates grounded longitudinal retrieval; it is not broad evidence for better hiring outcomes, and reported scores are not imported into this application.

## Validation status

Unit tests check source chunk integrity and stable IDs, report budget handling, retention of projects/facts and a simple relevance example. Local quant and Agent JD checks verify auditable retrieval and reduced context size. They do not measure semantic recall, ranking superiority, hiring outcomes or real ATS behavior. Those require separate labelled comparisons and review.
