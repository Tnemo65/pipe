# THESIS OUTLINE — Writing Guide

A comprehensive guide for writing each section of a thesis at the University of Engineering and Technology (UET), Vietnam National University Hanoi. Based on analysis of 2 thesis templates.

---

## THESIS STRUCTURE OVERVIEW

```
FRONT MATTER
  Title Page → Acknowledgements → Authorship → Abstract + Tom tat
  → Table of Contents → List of Figures → List of Tables → List of Abbreviations

MAIN CONTENT
  Introduction (NOT a chapter)
    1.1 Context of the Research
    1.2 Research Challenges
    1.3 Thesis Objective and Main Contents
    1.4 Thesis Structure

  Chapter 1: Fundamental Theories
    1.1 [Theory Topic 1]
    1.2 [Theory Topic 2]
    1.3 Role and Practical Applications
    1.4 Chapter Summary

  Chapter 2: Proposed System Architecture
    2.1 Related Work and Base Architecture
    2.2 Core Layers of the Data Platform
    2.3 Technology Architecture
    2.4 Chapter Summary

  Chapter 3: Experiments and Evaluation
    3.1 Experimental Environment
    3.2 Service Integration
    3.3 Results and Evaluation
    3.4 Chapter Summary

BACK MATTER
  Conclusion and Perspectives
    Main Contributions
    Thesis Limitations
    Future Work
  References
  Appendices
```

---

## 1. INTRODUCTION

> **Khong phai mot chuong** — phan INTRODUCTION dung truoc Chuang 1.

### 1.1 Context of the Research (Boi cuh)

- **Muc dich**: Dai bieu 1-2 doan van, 150-250 words. DAt bieu bai toan va bai canh rong.
- **Noi dung**:
  - Bối cảnh thế giới/ngành: ví dụ "Trong thời đại số, các tổ chức đang tạo ra lượng dữ liệu ngày càng lớn..."
  - Xu hướng: IoT, mạng xã hội, giao dịch tài chính...
  - Vấn đề: dữ liệu phân tán, không nhất quán, silo dữ liệu
  - Dẫn số liệu: IDC (Global Datasphere 175 ZB by 2025), Gartner (74% dữ liệu chưa được phân tích)
- **Viết**: Present tense, passive voice, formal academic style.

**Mẫu** (trích từ thesis 2023):
> "In today's digital world, organizations are generating and collecting more data than ever before. This data comes from a variety of sources such as IoT devices, social media, and customer interactions, and is stored in different formats and locations such as databases, cloud storage, and on-premises systems."

**Mẫu** (trích từ thesis 2026):
> "In today's digital age, organizations use and store an increasing amount of data from a variety of sources, including social networks, IoT devices, and financial transactions."

### 1.2 Research Challenges (Thách thức nghiên cứu)

- **Muc dich**: 1-2 doan van, trinh bay cac van de cu the can giai quyet.
- **Noi dung**:
  - Thách thức 1: Dữ liệu phân tán, nhiều nguồn khác nhau
  - Thách thức 2: Thiếu công cụ mã nguồn mở toàn diện
  - Thách thức 3: Khó khăn trong truy vấn và phân tích
  - Thách thức 4: Chi phí giải pháp thương mại cao, rủi ro bảo mật
- **Viết**: Present tense, formal, "Despite...", "However...", "Therefore..."

**Mẫu**:
> "Despite the development of data technologies, public research on solutions related to metadata knowledge graphs is quite limited. Current popular solutions also revolve around paid commercial services. Therefore, there is a need for an open-source solution..."

### 1.3 Thesis Objective and Main Contents (Mục tiêu và nội dung)

- **Muc dich**: 1 doan + 4 bullet points.
- **Cấu trúc**:
  - Câu mở đầu: "The objective of this thesis is to..."
  - 4 bullet points cho main contents

**Mẫu**:
> "The objective of this thesis is to research, study, and build an open-source data platform solution based on [architecture type] that allows businesses and organizations to centrally manage distributed data.

> The main contents required to achieve the above objective include:
> - Introducing the definition of [topic], [subtopic] and benefits of integrating...
> - Designing the system architecture and technology stacks.
> - Implementing and installing the platform.
> - Evaluating the platform's effectiveness with a specific use case."

### 1.4 Thesis Structure (Cấu trúc luận văn)

- **Muc dich**: 1 doan + 1 description list.
- **Cấu trúc**: Mô tả từng chương (1 câu/mỗi chương).

**Mẫu**:
> "Apart from the introduction and conclusion, this thesis is organized into 3 main chapters with the following contents:
> - Chapter 1 introduces the background and fundamental concepts...
> - Chapter 2 describes the proposed data platform architecture...
> - Chapter 3 presents the experimental setup, implementation, and evaluation results...
> - Conclusion summarizes the main findings and outlines future directions."

---

## 2. CHAPTER 1: FUNDAMENTAL THEORIES

> Tùy đề tài, Chương 1 có thể là "Overview of Data Fabric" (thesis 2023) hoặc "Fundamental Theories" (thesis 2026).

### 2.1-2.3: Theory Sections (3 sub-sections)

Mỗi sub-section gồm:

- **Definition** (1 đoạn): Định nghĩa chuẩn academic, trích dẫn 2-3 nguồn.
- **Components/Structure** (1-2 đoạn): Các thành phần cốt lõi, có thể dùng bullet list.
- **Practical Applications** (1 đoạn): Ứng dụng thực tiễn, case studies.

**Mẫu Definition (Knowledge Graph)**:
> "A Knowledge Graph (KG) is a network representing real-world entities and relationships between them. Based on an original entity, the Knowledge Graph provides information about every other entity in the network... [cite: Hogan et al. 2021]"

**Mẫu Components**:
> "The [concept] consists of several key components: (1) Entities: real-world entities represented as nodes; (2) Relationships: edges defining connections; (3) Labels: attributes and properties; (4) Ontology/Schema: vocabularies and logical rules."

**Các tool gợi ý**: Thêm hình vẽ kiến trúc cho mỗi sub-section.

### 2.4: Chapter Summary

- **Muc dich**: 1 đoạn duy nhất, trinh bay tom tat.
- **Cấu trúc**:
  1. Recap: "This chapter provided an overview of [topics]"
  2. Key takeaways: 2-3 ý chính
  3. Transition: "This sets the stage for Chapter 2, where we will..."

**Mẫu**:
> "This chapter has provided a solid overview of Knowledge Graphs and Intelligent Analytics... Key components such as entities, relations, triples, and ontologies were discussed... This sets the stage for the following chapters, where we will explore the system architecture and specific implementation."

---

## 3. CHAPTER 2: PROPOSED SYSTEM ARCHITECTURE

> **Quan trọng nhất** — Chứa toàn bộ đóng góp kiến trúc.

### 3.1: Related Work and Base Architecture

- **3.1.1 Reference Architecture** (1-2 đoạn + hình): Giới thiệu framework tham chiếu (ví dụ: vDFKM).
- **3.1.2 Proposed High-Level Architecture** (2-3 đoạn + hình): Mô tả kiến trúc đề xuất, 5 tầng chính.

### 3.2: Core Layers of the Data Platform

7 sub-layers. Mỗi sub-layer:

| Sub-layer | Noi dung mo ta |
|---|---|
| 2.2.1 Data Source Layer | Loại nguồn dữ liệu (structured/semi/unstructured) |
| 2.2.2 Data Ingestion Layer | Batch vs. Streaming ingestion |
| 2.2.3 Data Storage and Lakehouse Layer | Object storage, Data Lake, Lakehouse |
| 2.2.4 Data Transformation Layer | Cleaning, normalization, aggregation |
| 2.2.5 Metadata and Knowledge Graph Layer | Data catalog, lineage, governance |
| 2.2.6 Analytics and Visualization Layer | BI tools, dashboards |
| 2.2.7 Data Flow in the Platform | Tổng hợp luồng dữ liệu |

**Mẫu mô tả Layer**:
> "The [Layer Name] is [one sentence description]. This layer performs [what it does]. [Key technology/tool] is used to [capability]. This layer enables [benefit]."

### 3.3: Technology Architecture

7 mục con, mỗi mục:

- **Mục đích**: Tại sao chọn công nghệ này
- **Kiến trúc**: Mô tả các thành phần (có thể dùng bullet)
- **Hình vẽ**: Screenshot cấu hình hoặc architecture diagram
- **Vai trò**: Công nghệ đóng góp gì vào hệ thống

**Mẫu**:
> "[Tool Name] is an open-source [type] that [what it does]. One of the key advantages of [tool] is [capability]. [Cites relevant documentation or paper]. The architecture of [tool] consists of: (1) Component A: [description]; (2) Component B: [description]; (3) Component C: [description]."

### 3.4: Chapter Summary

Tương tự Chương 1, 1 đoạn recapping + transition.

---

## 4. CHAPTER 3: EXPERIMENTS AND EVALUATION

### 3.1: Experimental Environment

- **3.1.1 Hardware and Software** (1 đoạn + bảng specs)
- **3.1.2 Technology Stack** (1 đoạn + bảng versions)

**Mẫu bảng**:
```
| Component | Tool | Version |
|---|---|---|
| Data Source | MySQL Server | 5.7 |
| Data Ingestion | Airbyte | 0.43 |
| Storage | MinIO | RELEASE.2023 |
```

### 3.2: Service Integration

7 mục con, mỗi mục = 1 tool/service tích hợp.

Cấu trúc đề xuất cho mỗi mục:

1. **Mục đích** (1 câu): Tại sao cần tích hợp
2. **Cấu hình** (1-2 đoạn): Chi tiết các bước cấu hình
3. **Hình ảnh** (2-4 hình):
   - Screenshot cấu hình
   - Screenshot kết quả
4. **Giải thích** (1 đoạn): Phân tích kết quả

**Quy tắc quan trọng**:
- Luôn có hình ảnh (screenshot cấu hình hoặc kết quả)
- Mỗi hình: đánh số, caption, nguồn
- Screenshot: chụp từ giao diện thực tế

### 3.3: Results and Evaluation

- **3.3.1 Use Case Scenario** (2-3 trang):
  - Mô tả kịch bản (lĩnh vực: trường học, bệnh viện, bán lẻ...)
  - Dataset (bao nhiêu bảng, bao nhiêu records)
  - End-to-end pipeline (hình vẽ data lineage)
  - Dashboard kết quả (hình)

- **3.3.2 Evaluation** (1-2 trang):
  - Bảng tổng hợp metrics
  - Key findings (3-4 bullet points)

**Mẫu Evaluation**:
> "The experiment demonstrates the system's capability to [capabilities]. It successfully meets the defined requirements and shows potential for handling [scope]. Key findings: (1) The platform can easily handle scenarios where the data source contains from a few thousand to millions of records; (2) The integrated components form a unified platform..."

### 3.4: Chapter Summary

1 đoạn: recapping experiments + transition.

---

## 5. CONCLUSION AND PERSPECTIVES

### 5.1: Main Contributions (3-4 bullet points)

**Mẫu**:
> "In this thesis, we have [what you did]. The main contributions of this study include:
> - [Contribution 1]: [Description]. This provides [theoretical foundation / practical innovation].
> - [Contribution 2]: [Description]. This represents [core innovation].
> - [Contribution 3]: [Description]. This demonstrates [practical feasibility].
> - [Contribution 4]: [Description]. This validates [approach through experiments]."

### 5.2: Thesis Limitations (3-4 bullet points)

**Quy tắc**: Thành thật, không che giấu. Mỗi hạn chế nên có hướng khắc phục.

**Mẫu**:
> "Despite receiving valuable guidance from the supervisor, due to limited knowledge and time constraints, the platform development has not been optimized. Some areas that need further improvement include:
> - [Limitation 1]: [Description]. This limitation affects [aspect], and could be addressed by [proposed solution].
> - [Limitation 2]: [Description]..."

### 5.3: Future Work (3-4 bullet points)

**Mẫu**:
> "With further guidance, the platform will be incrementally optimized... Future directions include:
> 1. [Direction 1]: [Description]. This would enable [capability]...
> 2. [Direction 2]: [Description]..."

---

## 6. REFERENCES

### 6.1: Citation Rules

- **Format**: Square brackets, sequential numbering: `[1]`, `[2]`, `[3]`
- **Style**: `plainnat` (VNU standard) — author-year hoặc numeric tùy yêu cầu
- **Số lượng gợi ý**: 30-50 references cho 1 thesis

### 6.2: Reference Categories

| Category | Ví dụ | Số lượng |
|---|---|---|
| Books | O'Reilly, Springer, MIT Press | 5-8 |
| Conference Papers | IEEE, ACM, Springer | 8-12 |
| Journal Articles | IEEE TKDE, ACM TODS | 5-8 |
| Technical Docs | Apache, Docker, GitHub | 5-8 |
| Web Sources | Google, Microsoft, AWS blogs | 3-5 |

### 6.3: BibTeX Entry Types

```bibtex
@book{key2023,
  title     = {Book Title},
  author    = {Author, Name},
  year      = {2023},
  publisher = {Publisher Name},
  isbn      = {978-xxx-xxx-xxx-x}
}

@inproceedings{key2023,
  title     = {Paper Title},
  author    = {Author, A. and Author, B.},
  booktitle = {Conference Name},
  pages     = {1--10},
  year      = {2023},
  publisher = {IEEE}
}

@article{key2023,
  title     = {Article Title},
  author    = {Author, A.},
  journal   = {Journal Name},
  volume    = {10},
  number    = {1},
  pages     = {1--20},
  year      = {2023},
  doi       = {10.xxx/xxxxx}
}

@misc{key2023,
  title     = {Title},
  author    = {Organization},
  year      = {2023},
  url       = {https://example.com},
  note      = {Accessed: 2023-04}
}
```

---

## 7. WRITING RULES SUMMARY

### 7.1: Style Guidelines

| Rule | Description |
|---|---|
| Voice | Passive voice preferred in academic writing |
| Tense | Present tense for facts, past tense for experiments |
| Length | Section: 3-5 paragraphs (150-300 words); Chapter: 15-30 pages |
| Citations | `[number]` sequential, never skip numbers |
| Acronyms | Define on first use: "Structured Query Language (SQL)" |
| Figures | Always number + caption above, source below |
| Tables | Always number + caption above |
| References | Always list in References section, cite in text |

### 7.2: Chapter Summary Template

> "This chapter has provided [overview]. We began by defining [concept] as [brief definition], emphasizing [key points]. Key components such as [list] were discussed, highlighting their roles in [what they enable]. [Second half summary]. This sets the stage for the following chapters, where we will explore [next chapter topic]."

### 7.3: Figure and Table Rules

**Figures**:
- Caption above: "Figure X.Y: Description of the figure"
- Source below (if applicable): "Source: [reference or own creation]"
- Size: 0.7-0.85 textwidth
- Format: PNG or PDF for crisp rendering

**Tables**:
- Caption above: "Table X.Y: Description"
- Use `booktabs` style (no vertical lines, horizontal lines only)
- Header row: bold or shaded
- Units in column headers when applicable

### 7.4: Common Academic Phrases

| Situation | Phrase |
|---|---|
| Claiming contribution | "To the best of our knowledge, we are the first to..." |
| Acknowledging limitation | "While beyond the scope of this paper, future work could..." |
| Transition to next section | "This sets the stage for..." |
| Citing | "According to [Author, Year]..." |
| Contrasting | "Unlike [prior work] which [limitation], our approach..." |

---

## 8. FIGURE/PLACEMENT GUIDELINES

| Chapter | Số lượng hình tối thiểu | Loại hình |
|---|---|---|
| Chương 1 | 1-2 | Architecture diagrams, component diagrams |
| Chương 2 | 5-7 | Reference arch, proposed arch, data flow, tool arch (x4), KG diagram |
| Chương 3 | 8-12 | Screenshots (config, results, dashboards), data lineage, evaluation charts |

---

## 9. ESTIMATED PAGE COUNT

| Section | Pages |
|---|---|
| Front Matter (Title, Acknowledgements, Abstract, TOC) | 10-15 |
| Introduction (Context + Challenges + Objectives + Structure) | 4-6 |
| Chapter 1 (Fundamental Theories) | 15-25 |
| Chapter 2 (Proposed Architecture) | 25-40 |
| Chapter 3 (Experiments) | 20-35 |
| Conclusion | 3-5 |
| References | 5-8 |
| Appendices | 5-15 |
| **Total** | **~80-150 pages** |

---

## 10. KEY DIFFERENCES: Data Fabric vs. Knowledge Graph Thesis

| Aspect | Data Fabric (2023) | Knowledge Graph (2026) |
|---|---|---|
| Chapter 1 Focus | Data Fabric components | KG definition, structure, construction |
| Chapter 2 Layer 7 | (none) | LLM-Powered Analytics |
| Technology | Airbyte, Delta Lake | Debezium, Kafka, Apache Hudi |
| LLM Integration | No | Yes (GPT-4o for dashboard generation) |
| Dataset | Business scenarios (sale, game, staff) | University academic data |
| Use Cases | 3 scenarios | 1 end-to-end scenario |
