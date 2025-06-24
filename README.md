# RootOmics

RootOmics is a functional enzyme database for microbial ecology, cataloging soil nutrient-cycling enzymes with detailed annotations.  
**Team:** Anuradha Basyal, Adithi Nataraaj, Shivani Pimparkar  
**Advisor:** Jennifer Bhatnagar, Associate Professor of Biology, Boston University

---

## What is RootOmics?

RootOmics is a functional enzyme database designed for microbial ecology research. It catalogs soil nutrient-cycling enzymes involved in carbon, nitrogen, and phosphorus transformations, with detailed annotations (EC, KO, GO) and pathway mappings. By integrating genomic and experimental data, it helps researchers assess enzyme distribution, pathway completeness, and functional potential across diverse soil microbial communities. Developed by Team 13 at Boston University (BF768, Spring 2024), RootOmics supports bioinformatics workflows, genomic analyses, and environmental functional gene studies, enabling insights into biogeochemical cycling and microbial ecosystem functions.

---

## Motivation and Background

- Soil microbes drive global biogeochemical cycles, but their extracellular molecular functions are under-characterized.
- KEGG and GO focus mostly on intracellular processes, leaving environmental gene function under-characterized.
- No comprehensive tool links gene presence to ecological roles in soil.
- RootOmics bridges this gap, enabling new insights into how enzymes respond to environmental stressors and drive nutrient cycling.

---

## What Can RootOmics Help Us Answer?

- How do enzymes respond to environmental stressors?
- What evidence supports a specific enzyme’s role in nutrient cycling?
- What are the dominant enzymes driving C, N, and P transformations in soil?

---

## Database Structure & Accessibility

- **Open access and searchable**—no login required.
- Each entry includes EC number, enzyme name, function, and evidence source.
- Contributor uploads are reviewed to ensure data quality.

### Data Model

- **Proteins:** Protein name, enzyme type, EC numbers, KO numbers, GO terms
- **Pathways:** KEGG pathway, CAZyme class/superfamily
- **Ecosystem Processes:** Broad ecological process linked to proteins

**Entity relationships** are managed via linking tables for many-to-many associations, enabling robust queries and flexible data exploration.

---

## Web Interface

- **Explorer:** Search/filter proteins by name, enzyme type, EC/KO/GO numbers, or pathway
- **Download:** Export filtered results as CSV or Excel
- **Contact:** Submit suggestions or new datasets via a contact form
- **Help Center:** Quick tips and guidance for using the database

---

## Sample SQL Queries

-- 1) Search by protein name ("oxidase") and return full annotation
SELECT
p.Protein_name,
p.Enzyme_Type,
p.EC_numbers,
p.KO_Numbers,
p.GO_terms,
GROUP_CONCAT(DISTINCT pw.KEGG_pathway) AS Pathways,
GROUP_CONCAT(DISTINCT ep.Broad_Process) AS Ecosystem_Processes
FROM Proteins p
LEFT JOIN Protein_Pathway pp ON p.PID = pp.PID
LEFT JOIN Pathways pw ON pp.PAID = pw.PAID
LEFT JOIN Protein_Ecosystem_Process pep ON p.PID = pep.PID
LEFT JOIN Ecosystem_Processes ep ON pep.EID = ep.EID
WHERE p.Protein_name LIKE '%oxidase%'
GROUP BY p.PID
LIMIT 100;

-- 2) Filter by EC number (e.g. "3.2.1.14")
SELECT
p.Protein_name,
p.Enzyme_Type,
p.EC_numbers
FROM Proteins p
WHERE p.EC_numbers LIKE '%3.2.1.14%'
LIMIT 100;

-- 3) Combine protein name and KEGG pathway filter
SELECT
p.Protein_name,
GROUP_CONCAT(DISTINCT pw.KEGG_pathway) AS Pathways
FROM Proteins p
JOIN Protein_Pathway pp ON p.PID = pp.PID
JOIN Pathways pw ON pp.PAID = pw.PAID
WHERE p.Protein_name LIKE '%oxidase%'
AND pw.KEGG_pathway = '00010' -- Glycolysis / Gluconeogenesis
GROUP BY p.PID;

text

---



## Data Download

- Use the "Download" tab in the web interface to export your filtered data as CSV or Excel files for further analysis.

---

## Contributing

- Contributions are welcome! Please submit a pull request or use the contact form for suggestions and new datasets.
- All contributor uploads are reviewed for data quality before inclusion.

---

## Contact

Questions or suggestions? Use the Contact tab in the web interface or email the project advisor:  
Dr. Jennifer Bhatnagar, Associate Professor of Biology, Boston University

---

