# Local library and assembly formats

Paths in newly imported source records are relative to DATA. Legacy libraries may contain absolute source paths. Preserve those records and existing IDs when editing. The script imports materials into `materials/`, templates into `templates/`, and each PDF version into `outputs/`. It backs up `library.json` under `backups/` before updates.

## Library

Keep the existing top-level structure. This synthetic example shows the supported fields.

```json
{
  "schema_version": 2,
  "profile": {
    "name": "Example Candidate",
    "contact": "candidate@example.com",
    "education": ["Example University, Computer Science, 2024–2028"],
    "skills": ["Python, NumPy, PyTorch"],
    "awards": [],
    "availability": "4 days per week",
    "publications": [],
    "certifications": []
  },
  "projects": [
    {
      "id": "project-forecast",
      "title": "Demand forecasting research",
      "date": "2026.01–2026.05",
      "tags": "Python, time series, evaluation",
      "source": "Local research report",
      "contribution_status": "user-confirmed",
      "facts": [
        {
          "id": "forecast-f1",
          "text": "Implemented chronological evaluation on 12 weeks of held-out demand data.",
          "source_ids": ["source-material-example"],
          "status": "confirmed"
        }
      ],
      "reports": [
        {
          "id": "forecast-report-v1",
          "title": "Forecasting experiment report",
          "content": "Complete report with background, personal contribution, data, methods, baselines, results and limitations.",
          "source_ids": ["source-material-example"],
          "status": "reviewed"
        }
      ]
    }
  ],
  "sources": [],
  "template": "public"
}
```

`sources` is populated by `import`. Copy the returned IDs into relevant `source_ids` arrays. A source record contains its original location, archived copy, SHA-256, capture time and, when available, extracted-text path. Import does not interpret claims or create project facts automatically.

Use reports as full research or project archives. Include the question, motivation, personal role, completed implementation, dataset and split, environment, experiment setup, baseline, numerical results with units, failures, limitations and supporting artifacts when available. Keep unknown details explicitly unknown. Record publication status and confirmed authorship for papers, and issuer and award date for certificates. Standalone papers and certificates can use the optional profile lists shown above. Relevant research papers may also support a project's report and facts. Employment can be recorded with `kind: "employment"` in a project-shaped record so its contributions can be selected; preserve employer and role in its title and full report.

Keep stable IDs when rewording the same fact without changing its meaning. A changed result or new experiment receives a new fact ID. Preserve the prior version with `status: "superseded"` and a `superseded_by` ID, and use the current supported fact in assemblies. Reports store Markdown directly in `content`; retain full text or an archived source for future tailoring. Existing library metadata remains valid even when absent from this example.

Before direct edits, run `init` to create a backup, then read the latest library. Write a sibling temporary JSON file, parse it to confirm valid JSON and atomically replace `library.json`. Serialize mutations to a shared data directory. This version targets one user's local workflow.

## Assembly

```json
{
  "role": "Research Intern",
  "selected": [
    {
      "id": "project-forecast",
      "reason": "Demonstrates the JD's chronological evaluation requirement.",
      "bullets": [
        {
          "text": "Implemented chronological evaluation on 12 weeks of held-out demand data.",
          "evidence": ["forecast-f1"]
        }
      ]
    }
  ],
  "gaps": ["No confirmed deployment experience in the supplied materials."],
  "omitted": []
}
```

Each selected `id` must exist in the library. Each bullet's nonempty `evidence` array must cite facts or reports from that project. Keep each bullet within 450 characters and select at most five projects. Education, skills, awards and optional publications/certificates come from `profile`. The visible PDF excludes reasons, gaps and reference IDs; they remain in `assembly.json`.

The renderer mechanically checks numeric tokens against cited evidence. For example, write a source value of `7,266` as `7,266` or `7266`, rather than converting it into a rounded figure or calculating a new percentage in the resume. Ask for evidence of a derived result or add its documented calculation to the project report first. These checks do not establish the meaning or truth of a claim.

## Templates

The public template is included in `assets/public.tex` and uses standard TeX-distributed fonts. Import custom templates with `--kind template` from a LaTeX ZIP. `resume`-class templates retain the header before the first section. Other templates require `{{CONTENT}}` in the document body. Content uses standard section, subsection and itemize commands. Test compatibility by rendering.

Optional header markers `{{NAME}}`, `{{CONTACT}}`, `{{ROLE}}` and `{{AVAILABILITY}}` are replaced by escaped current values. Hardcoded template headers retain their uploaded text, so inspect them before rendering for another candidate or role. Compilation uses Tectonic `--untrusted`. Template ZIPs containing executable scripts are rejected. This version imports DOCX as evidence text; custom template rendering supports LaTeX ZIP.
