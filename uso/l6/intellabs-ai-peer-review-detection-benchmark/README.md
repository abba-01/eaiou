---
configs:
- config_name: calibration
  data_files:
  - split: GPT4o
    path: calibration/gpt4o/*.csv
  - split: Gemini_1.5_Pro
    path: calibration/gemini/*.csv
  - split: Claude_Sonnet_3.5
    path: calibration/claude/*.csv
  - split: Llama_3.1_70b
    path: calibration/llama/*.csv
  - split: Qwen_2.5_72b
    path: calibration/qwen/*.csv
- config_name: test
  data_files:
  - split: GPT4o
    path: test/gpt4o/*.csv
  - split: Gemini_1.5_Pro
    path: test/gemini/*.csv
  - split: Claude_Sonnet_3.5
    path: test/claude/*.csv
  - split: Llama_3.1_70b
    path: test/llama/*.csv
  - split: Qwen_2.5_72b
    path: test/qwen/*.csv
- config_name: extended
  data_files:
  - split: GPT4o
    path: extended/gpt4o/*.csv
  - split: Llama_3.1_70b
    path: extended/llama/*.csv

license: other
license_name: intel-research-development-license
license_link: LICENSE.md
---

# Dataset Card for AI Peer Review Detection Benchmark

## Dataset Summary
The AI Peer Review Detection Benchmark dataset is the largest dataset to date of paired human- and AI-written peer reviews for identical research papers. It consists of 788,984 reviews generated for 8 years of submissions to two leading AI research conferences: ICLR and NeurIPS. Each AI-generated review is produced using one of five widely-used large language models (LLMs), including GPT-4o, Claude Sonnet 3.5, Gemini 1.5 Pro, Qwen 2.5 72B, and Llama 3.1 70B, and is paired with corresponding human-written reviews. The dataset includes multiple subsets (calibration, test, extended) to support systematic evaluation of AI-generated text detection methods. 

## Dataset Details

- **Creators**: Intel Labs
- **Version**: v1.0
- **License**: [Intel OBL Internal R&D Use License Agreement](LICENSE.md)
- **Number of Calibration (Training) Samples**: 75,824
- **Number of Test Samples**: 287,052
- **Number of Extended Samples**: 426,108
- **Total Samples**: 788,984
- **Format**: CSV
- **Fields**: CSV files may differ in their column structures across conferences and years due to updates in review templates; see Table 5 in the paper for review fields of individual conferences.

## Intended Use

- **Primary Uses**:
  - Research use only
  - Benchmarking and developing detection methods for AI-generated peer reviews
  - Analyzing differences between human and AI review content
- **Out-of-Scope Uses**:
  - Use in non-research or commercial contexts
  - Deployment in real-world systems for automated review detection
  - Use cases that may contribute to misuse of peer review or compromise research integrity (e.g., training language models to mimic peer review quality without safeguards)

## Data Collection Process
Human-written reviews were collected from public sources via the OpenReview API (ICLR 2019–2024, NeurIPS 2021–2024) and the ASAP-Review dataset (ICLR 2017–2018, NeurIPS 2016–2019). AI-generated reviews were created by prompting five LLMs with the original paper text, conference-specific reviewer guidelines and review templates aligned. Commercial API services and on-prem hardware (Intel Gaudi and NVIDIA GPU) were used for AI review generation.

All reviews provided from [OpenReview.net](https://openreview.net/legal/terms) are provided under the [Creative Commons Attribution 4.0 International](http://creativecommons.org/licenses/by/4.0/) license.  Reviews provided by the [ASAP-Review Dataset](https://github.com/neulab/ReviewAdvisor#dataset) are provided under the [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) license.

## Ethical Considerations
Intel is committed to respecting human rights and avoiding causing or contributing to adverse impacts on human rights. See [Intel’s Global Human Rights Principles](https://www.intel.com/content/dam/www/central-libraries/us/en/documents/policy-human-rights.pdf). Intel’s products and software are intended only to be used in applications that do not cause or contribute to adverse impacts on human rights.

## Contact Information

- **Issues**: For any issues or questions regarding the dataset, please contact the maintainers or open an issue in the dataset repository.

## [Dataset Citation]

If you use this dataset in your work, please cite the following [**paper**](https://arxiv.org/abs/2502.19614):
```
@misc{yu2025paperreviewedllmbenchmarking,
      title={Is Your Paper Being Reviewed by an LLM? Benchmarking AI Text Detection in Peer Review}, 
      author={Sungduk Yu and Man Luo and Avinash Madusu and Vasudev Lal and Phillip Howard},
      year={2025},
      eprint={2502.19614},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2502.19614}, 
}
```

## [Extra Information]

### File Naming Convention
Each file is named using the format: `<subset_name>.<conference_name>.<LLM_name>.csv`.
For example, `ICLR2017.calibration.claude-sonnet-3.5v2.csv` represents samples generated for the **ICLR 2017** conference by **Claude Sonnet 3.5**, specifically for the **calibration subset**.

### Dataset File Structure
The calibration, test, and extended sets are in separate directories. Each directory contains subdirectories for different models that were used to generate AI peer review samples. In each model's subdirectory, you will find multiple CSV files, with each file representing peer review samples of a specific conference. The directory and file structure are outlined below.
```
|-- calibration
    |-- claude
        |-- ICLR2017.calibration.claude-sonnet-3.5v2.csv
        |-- ...
        |-- ICLR2024.calibration.claude-sonnet-3.5v2.csv
        |-- NeurIPS2016.calibration.claude-sonnet-3.5v2.csv
        |-- ...
        |-- NeurIPS2024.calibration.claude-sonnet-3.5v2.csv
    |-- gemini
        |-- ...
    |-- gpt4o
        |-- ...
    |-- llama
        |-- ...
    |-- qwen
        |-- ...
|-- extended
    |-- gpt4o
        |-- ICLR2018.extended.gpt-4o.csv
        |-- ...
        |-- ICLR2024.extended.gpt-4o.csv
        |-- NeurIPS2016.extended.gpt-4o.csv
        |-- ...
        |-- NeurIPS2024.extended.gpt-4o.csv
    |-- llama
        |-- ...
|-- test
    |-- claude
        |-- ICLR2017.test.claude-sonnet-3.5v2.csv
        |-- ...
        |-- ICLR2024.test.claude-sonnet-3.5v2.csv
        |-- NeurIPS2016.test.claude-sonnet-3.5v2.csv
        |-- ...
        |-- NeurIPS2024.test.claude-sonnet-3.5v2.csv
    |-- gemini
        |-- ...
    |-- gpt4o
        |-- ...
    |-- llama
        |-- ...
    |-- qwen
        |-- ...
```

### CSV File Content
CSV files may differ in their column structures across conferences and years. These differences are due to updates in the required review fields over time as well as variations between conferences. See the table below for the review fields of individual conferences.

| Conference    | Required Fields                                                                                                                                                          |
|---------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ICLR2017      | review, rating, confidence                                                                                                                                               |
| ICLR2018      | review, rating, confidence                                                                                                                                               |
| ICLR2019      | review, rating, confidence                                                                                                                                               |
| ICLR2020      | review, rating, confidence, experience assessment, checking correctness of derivations and theory, checking correctness of experiments, thoroughness in paper reading |
| ICLR2021      | review, rating, confidence                                                                                                                                               |
| ICLR2022      | summary of the paper, main review, summary of the review, correctness, technical novelty and significance, empirical novelty and significance, flag for ethics review, recommendation, confidence |
| ICLR2023      | summary of the paper, strength and weaknesses, clarity quality novelty and reproducibility, summary of the review, rating, confidence                                     |
| ICLR2024      | summary, strengths, weaknesses, questions, soundness, presentation, contribution, flag for ethics review, rating, confidence                                                |
| NeurIPS2016   | review, rating, confidence                                                                                                                                               |
| NeurIPS2017   | review, rating, confidence                                                                                                                                               |
| NeurIPS2018   | review, overall score, confidence score                                                                                                                                  |
| NeurIPS2019   | review, overall score, confidence score, contribution                                                                                                                  |
| NeurIPS2021   | summary, main review, limitations and societal impact, rating, confidence, needs ethics review, ethics review area                                                         |
| NeurIPS2022   | summary, strengths and weaknesses, questions, limitations, ethics flag, ethics review area, rating, confidence, soundness, presentation, contribution                      |
| NeurIPS2023   | summary, strengths, weaknesses, questions, limitations, ethics flag, ethics review area, rating, confidence, soundness, presentation, contribution                      |
| NeurIPS2024   | summary, strengths, weaknesses, questions, limitations, ethics flag, ethics review area, rating, confidence, soundness, presentation, contribution                      |

