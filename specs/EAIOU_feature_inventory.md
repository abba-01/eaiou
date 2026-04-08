# 0\. these are preliminary brainstorms. YOu need to vcreae a SSOT from this si we ccan build the website jourmnal up from Joomla 5.3 under LAMP stack using the JOomla artivcle system. acl as teh foundation for th4 journal;, adding to the acl, and using the acl rather than repcle it and using 4h article systems as is and adding to tits core functions usiong custom plugins per feature so we can easily debug lets say research-endpoints) 

# 1.) Treat things that can talk like humanity.

# 

# 2\. (not exhaustiove)EAIOU Feature Inventory (from SQL)

## eaiou\_papers

* CRUD: create/read/update/delete records for this entity
* Publishing state toggle (state)
* Access level control (access)
* Sortable ordering (ordering)
* Audit fields (created/modified/checked\_out timestamps and users)
* Paper metadata (title, abstract, authors, doi)
* Authorship tracking (authorship\_mode)
* Submission lifecycle fields (status, submission/acceptance/publication dates)
* Version tagging (submission\_version)

## eaiou\_remsearch

* CRUD: create/read/update/delete records for this entity
* Publishing state toggle (state)
* Access level control (access)
* Sortable ordering (ordering)
* Audit fields (created/modified/checked\_out timestamps and users)
* Relations: paper\_id (link to parent records)
* Literature triage (citation\_title/source/link)
* Inclusion triage (used flag, reasons)
* Source typing (source\_type)

## eaiou\_ai\_sessions

* CRUD: create/read/update/delete records for this entity
* Publishing state toggle (state)
* Access level control (access)
* Sortable ordering (ordering)
* Audit fields (created/modified/checked\_out timestamps and users)
* Relations: paper\_id (link to parent records)
* AI session labeling (session\_label, ai\_model\_name)
* Session timing (start\_time, end\_time) and token counts
* Redaction workflow (redaction\_status, session\_notes, session\_hash)

## eaiou\_didntmakeit

* CRUD: create/read/update/delete records for this entity
* Publishing state toggle (state)
* Access level control (access)
* Sortable ordering (ordering)
* Audit fields (created/modified/checked\_out timestamps and users)
* Relations: session\_id (link to parent records)
* Excluded prompt/response archival
* Redaction tracking (redacted, redaction\_hash)

## eaiou\_plugins\_used

* CRUD: create/read/update/delete records for this entity
* Publishing state toggle (state)
* Access level control (access)
* Sortable ordering (ordering)
* Audit fields (created/modified/checked\_out timestamps and users)
* Relations: paper\_id (link to parent records)
* Plugin/tool audit (plugin\_name, plugin\_type, execution\_context)
* Execution logs per run

## eaiou\_review\_logs

* CRUD: create/read/update/delete records for this entity
* Publishing state toggle (state)
* Access level control (access)
* Sortable ordering (ordering)
* Audit fields (created/modified/checked\_out timestamps and users)
* Relations: paper\_id, reviewer\_id (link to parent records)
* Peer review event log (review\_date, reviewer\_id, version\_reviewed)
* Review rubric (overall, originality, methodology, transparency, AI disclosure)
* Narrative notes (review\_notes)

## eaiou\_versions

* CRUD: create/read/update/delete records for this entity
* Publishing state toggle (state)
* Access level control (access)
* Sortable ordering (ordering)
* Audit fields (created/modified/checked\_out timestamps and users)
* Relations: paper\_id (link to parent records)
* Version labeling \& file path
* AI authorship flag + model name
* Generation date and notes

## eaiou\_attribution\_log

* CRUD: create/read/update/delete records for this entity
* Publishing state toggle (state)
* Access level control (access)
* Sortable ordering (ordering)
* Audit fields (created/modified/checked\_out timestamps and users)
* Relations: paper\_id (link to parent records)
* Attribution entries (contributor\_name, role\_description, contribution\_type)
* AI/human authorship booleans
* Timestamped linkage to paper/version
* Tool reference (ai\_tool\_used)

## eaiou\_api\_keys

* CRUD: create/read/update/delete records for this entity
* Publishing state toggle (state)
* Access level control (access)
* Sortable ordering (ordering)
* Audit fields (created/modified/checked\_out timestamps and users)
* Relations: user\_id (link to parent records)
* API key registry (api\_key, description)
* Key owner (user\_id) and status
* Access tiering (access\_level)

## eaiou\_api\_logs

* CRUD: create/read/update/delete records for this entity
* Publishing state toggle (state)
* Access level control (access)
* Sortable ordering (ordering)
* Audit fields (created/modified/checked\_out timestamps and users)
* Relations: api\_key\_id (link to parent records)
* API call audit (endpoint, request\_data, response\_code, timestamp)
* Key linkage (api\_key\_id)

-----------------------------------------



Features of peer review websites

Peer review websites, primarily used in academic publishing, facilitate the submission, review, and publication process for scholarly work. 

Key features include:

1\. Author submission portal

Allows authors to upload manuscripts, supplementary files, and essential metadata.

Supports various formats for manuscripts, figures, and supplemental materials, including Microsoft Word, TeX, PDF, TIFF, EPS, BMP, PNG, JPG, and video, audio, and data sets.

Provides real-time status updates on submissions and streamlines the process through an intuitive interface. 

2\. Peer review management

Facilitates the selection and assignment of reviewers.

Tracks review progress and enables reviewers to submit feedback.

Supports different peer review models, including single-blind, double-blind, transparent, collaborative, and post-publication review.

Ensures confidentiality and protects against reviewer bias through features like anonymized review processes and conflict of interest disclosures.

Provides tools and guidelines to assist reviewers in delivering constructive and ethical feedback, according to Yomu AI. 

3\. Editorial workflow

Allows editors to make decisions, communicate with authors, and manage revisions.

Manages the communication between authors, reviewers, and editors through integrated email systems and automated notifications.

Offers dashboards and reports for tracking progress and analyzing metrics like response times and review quality. 

4\. Integrity and quality assurance

Integrates with plagiarism detection tools and formatting checks to enforce journal-specific guidelines.

Uses reviewer databases to select qualified reviewers and monitor their performance.

Offers features like co-author verification to prevent misconduct like ghost or gift authorship. 

5\. Other important features

Automated correspondence and reminders for deadlines and decisions.

Integration with research databases like ORCID and CrossRef for author identification and citation linking.

Open-source platforms (like Open Journal Systems) offer flexibility and customization for smaller journals and academic institutions. 

In essence, these websites are designed to streamline the peer review process, ensuring efficiency, quality, and integrity in academic publishing. 

AI responses may include mistakes. Learn more







What plagiarism detection tools are integrated into peer review websites?



Elaborate on features ensuring reviewer confidentiality and preventing bias



How do peer review websites handle manuscript revisions?



undefined

undefined

undefined

11 sites

How To Use Manuscript Submission Systems for Papers

Jul 18, 2024 — What Are Manuscript Submission Systems? Manuscript submission systems are online platforms designed to facilitate the submission, review, and publication of res...

favicon

www.journal-publishing.com



Editorial Management System for peer review: online?

Oct 20, 2017 — Features to look for \* An online submission form for authors to submit manuscripts with metadata. \* A dashboard for editorial staff to track submissions at vari...

favicon

Manuscript Manager



Types of Peer Review - Wiley Author Services

Types of peer review. The three most common types of peer review are single-anonymized, double-anonymized, and open peer review. Peer review is constantly evolv...

favicon

Wiley Author Services

Show all

i need an ecxhaustive feature lizst

Exhaustive list of peer review website features

Peer review websites are crucial for the academic publishing lifecycle, offering a comprehensive suite of features that span from author submission to publication and reporting. These features aim to enhance the efficiency, transparency, and integrity of the peer review process. 

Here's an exhaustive list of key features:

1\. Author and reviewer management

Submission Portal: Intuitive interface for authors to submit manuscripts, including various file types (Word, PDF, LaTeX, figures, data sets, etc.).

Reviewer Databases: Maintain detailed profiles of potential reviewers, including their areas of expertise, review history, and performance metrics.

Conflict of Interest Checks: Features to identify and manage potential conflicts of interest among authors, reviewers, and editors.

Anonymization Options: Support for different peer review models, including single-blind, double-blind, and triple-blind, to ensure impartiality by masking identities, according to the University of California. 

2\. Editorial workflow and process management

Workflow Customization: Configurable workflows to adapt to specific journal requirements and processes.

Automated Assignment: Smart algorithms to match submissions with suitable reviewers based on expertise and workload.

Deadline Tracking and Reminders: Automated notifications and reminders for authors, reviewers, and editors to ensure timely progress.

Communication Tools: Built-in messaging systems and email templates to facilitate communication among all stakeholders.

Revision and Version Control: Tools to manage revisions, track changes, and maintain a history of manuscript versions.

Decision Management: Streamlined process for editors to make decisions (accept, reject, revise), communicate feedback, and manage revisions.

Editorial Board Management: Tools to manage editorial board members, their roles, and permissions. 

3\. Quality and integrity assurance

Plagiarism Detection: Integration with plagiarism detection services (like Crossref's Similarity Check) to screen submissions, according to scholasticahq.com.

Format Checking: Tools to ensure submitted manuscripts adhere to journal formatting guidelines.

Ethical Guidelines Enforcement: Features that support and enforce ethical guidelines for peer review, including reviewer guidelines and misconduct reporting.

Transparency and Open Peer Review Options: Support for transparent or open peer review models where review reports and author responses may be published alongside the accepted manuscript. 

4\. Reporting and analytics

Performance Tracking: Dashboards and reports to monitor key metrics, including submission-to-decision times, reviewer performance, and manuscript status.

Data Export: Options to export data for further analysis or archiving. 

5\. Security and data privacy

Secure Data Handling: Encryption of data in transit and at rest, strong authentication measures (e.g., two-factor authentication), and access control mechanisms.

Role-Based Permissions: Assigning granular permissions to users based on their roles (authors, reviewers, editors) to control data access.

Compliance: Adherence to data protection regulations like GDPR and HIPAA.

Data Backup and Recovery: Mechanisms for regular data backups and disaster recovery planning. 

6\. Integration and customization

Persistent Identifier Integration: Integration with ORCID and Crossref to uniquely identify authors and link publications and reviews.

Customizable Forms and Templates: Ability to create custom submission forms, review forms, and email templates.

Branding and Customization: Options to customize the platform's appearance and branding to align with journal identity. 

7\. Additional features

LMS Integration: Integration with learning management systems (LMS) for educational peer review scenarios.

Accessibility and Mobile Responsiveness: Ensuring the platform is accessible and usable across various devices and for individuals with disabilities. 

This comprehensive list highlights the many features that contribute to a robust and effective peer review website. 

AI responses may include mistakes. Learn more


Exhaustive list of peer review website features (with granular details)

1\. Author and reviewer management

1.1. Submission portal

1.1.1. File upload capabilities: Support for diverse file formats (e.g., Word, PDF, LaTeX, figures in TIFF, EPS, PNG, JPG, multimedia files like video/audio, and data sets).

1.1.2. Metadata capture: Fields for capturing essential metadata such as author information (including ORCID iDs), affiliations, keywords, abstract, and article type.

1.1.3. Submission form customization: Ability to add customized affirmations, file upload requirements, instructional text, CRediT (Contributor Role Taxonomy) fields, and more according to Scholastica.

1.1.4. Real-time status updates: Automated notifications and a dedicated interface for authors to track the progress of their submissions (e.g., received, under review, decision made).

1.1.5. Version control: Allows authors to upload revised manuscripts and supplementary materials while maintaining a clear history of previous versions.

1.2. Reviewer databases

1.2.1. Detailed reviewer profiles: Store information on reviewer expertise (using keywords or tagging functionality), institutional affiliations, contact information, and review history.

1.2.2. Performance tracking: Record metrics such as the number of completed reviews, average review completion time, number of on-time reviews, and decline rate.

1.2.3. Availability and workload management: Track reviewer availability and current workload to avoid over-inviting or assigning manuscripts that conflict with their schedules.

1.2.4. Conflict of interest tracking: Flag potential conflicts based on co-authorships, affiliations, or other relevant information.

1.2.5. Incentives and recognition: Integration with services like Publons or ReviewerCredits to acknowledge and reward reviewers for their contributions.

1.3. Conflict of interest checks

1.3.1. Automated detection: Flag potential conflicts based on keywords in submitted manuscripts or reviewer profiles.

1.3.2. Manual review and disclosure: Prompt authors, reviewers, and editors to disclose any potential conflicts of interest during the submission and review process.

1.3.3. Mitigation strategies: Tools to manage identified conflicts (e.g., re-assigning reviewers, informing the editorial board).

1.4. Anonymization options

1.4.1. Single-blind review: Masking reviewer identities from authors.

1.4.2. Double-blind review: Masking both author and reviewer identities from each other.

1.4.3. Triple-blind review: Masking author, reviewer, and editor identities from each other (less common but possible).

1.4.4. De-identification tools: Automated tools to remove identifying information from manuscripts and supplementary files to support blind review processes. 

2\. Editorial workflow and process management

2.1. Workflow customization

2.1.1. Configurable stages and statuses: Customize the different stages of the review process (e.g., initial check, reviewer invitation, review in progress, decision) and their associated statuses.

2.1.2. Role-based permissions: Define granular permissions for different user roles (e.g., editors, associate editors, journal administrators) at each workflow stage.

2.1.3. Automated actions: Automate tasks based on specific triggers (e.g., sending reviewer reminders, moving manuscripts to the next stage upon completion of reviews).

2.1.4. Adaptable templates: Create and customize templates for various communications (e.g., invitation letters, decision letters).

2.2. Automated assignment

2.2.1. Smart matching algorithms: Algorithms that suggest reviewers based on their areas of expertise (keywords, publication history), review performance, and current workload.

2.2.2. Load balancing: Distribute review invitations equitably among qualified reviewers.

2.2.3. Reviewer preferences: Factor in reviewer preferences (e.g., topics of interest, preferred review load) when suggesting assignments.

2.3. Deadline tracking and reminders

2.3.1. Configurable deadlines: Set deadlines for each stage of the review process (e.g., reviewer invitation response, review submission, revision submission).

2.3.2. Automated reminders: Send automated email reminders to authors, reviewers, and editors as deadlines approach or are missed.

2.3.3. Customizable notification frequency: Allow users to adjust the frequency of email reminders based on their preferences.

2.4. Communication tools

2.4.1. Secure messaging system: Built-in platform for secure communication between authors, reviewers, and editors, according to scholasticahq.com.

2.4.2. Email templates and personalization: Easily create and manage email templates for various correspondences (e.g., invitations, decision letters) with options for personalization.

2.4.3. Commenting and annotation tools: Enable reviewers to provide feedback directly on the manuscript within the platform.

2.5. Revision and version control

2.5.1. Track changes functionality: Allow authors and reviewers to track changes made to the manuscript during the revision process.

2.5.2. Version history and comparison: Maintain a clear history of all manuscript versions and offer tools to compare different versions.

2.5.3. Author response management: Provide a structured way for authors to respond to reviewer comments and indicate how they have addressed the feedback.

2.6. Decision management

2.6.1. Pre-defined decision options: Offer a range of decision options (e.g., accept, accept with minor revisions, accept with major revisions, revise and resubmit, reject).

2.6.2. Customizable decision letters: Create personalized decision letters that incorporate reviewer comments and editorial feedback.

2.6.3. Decision approval workflows: Require approval from senior editors or the editorial board for certain decisions.

2.7. Editorial board management

2.7.1. User role assignment: Assign specific roles (e.g., editor-in-chief, associate editor, guest editor) with corresponding permissions.

2.7.2. Performance tracking: Monitor the performance of editorial board members (e.g., decision-making speed, reviewer selection). 

3\. Quality and integrity assurance

3.1. Plagiarism detection

3.1.1. Integration with plagiarism detection services: Seamlessly connect with services like iThenticate to screen submissions for plagiarism, notes scholasticahq.com.

3.1.2. Similarity reports: Provide detailed reports highlighting instances of potential plagiarism.

3.1.3. Automated checks: Automate plagiarism screenings for all new submissions.

3.2. Format checking

3.2.1. Pre-submission checks: Automated tools to verify that submitted manuscripts adhere to journal-specific formatting guidelines (e.g., citation style, figure resolution).

3.2.2. Error notifications: Notify authors of any formatting errors detected during the submission process.

3.3. Ethical guidelines enforcement

3.3.1. Reviewer guidelines and codes of conduct: Provide clear guidelines for ethical conduct during peer review.

3.3.2. Misconduct reporting mechanisms: Offer channels for reporting suspected misconduct by authors, reviewers, or editors.

3.3.3. Co-author verification: Tools to verify the contributions of each author and prevent issues like ghost or gift authorship.

3.4. Transparency and open peer review options

3.4.1. Open reports: Publish review reports alongside the final published article.

3.4.2. Open identities: Allow authors and reviewers to be aware of each other's identities.

3.4.3. Post-publication commenting: Enable commenting and discussion on published articles, including the version of record. 

4\. Reporting and analytics

4.1. Performance tracking

4.1.1. Key metrics: Track metrics like submission-to-decision time, rejection rates, acceptance rates, and reviewer turnaround times.

4.1.2. Customizable dashboards: Provide interactive dashboards for visualizing key performance indicators.

4.1.3. Drill-down capabilities: Allow users to drill down into specific data points for more granular analysis.

4.2. Data export

4.2.1. Customizable reports: Generate reports in various formats (e.g., CSV, Excel) with customizable data fields.

4.2.2. API access: Provide API access for integrating with other systems and exporting data programmatically. 

5\. Security and data privacy

5.1. Secure data handling

5.1.1. Encryption: Encrypt data both in transit and at rest to protect sensitive information.

5.1.2. Access control: Implement granular, role-based access control mechanisms to restrict access to sensitive data and functionality.

5.1.3. Authentication: Support strong authentication methods, including multi-factor authentication.

5.2. Role-based permissions

5.2.1. Granular permission sets: Define fine-grained permissions for different user roles and workflow stages.

5.2.2. Customizable roles: Allow administrators to create custom roles and assign specific permissions based on organizational needs.

5.3. Compliance

5.3.1. Regulatory adherence: Ensure compliance with relevant data privacy regulations like GDPR and HIPAA.

5.3.2. Audit trails: Maintain detailed audit trails of user actions and system changes to support compliance and accountability.

5.4. Data backup and recovery

5.4.1. Automated backups: Implement automated backup procedures to regularly create copies of data and configuration settings.

5.4.2. Disaster recovery planning: Establish a disaster recovery plan to ensure business continuity in the event of data loss or system failure. 

6\. Integration and customization

6.1. Persistent identifier integration

6.1.1. ORCID integration: Connect with ORCID to uniquely identify authors and link their publications and reviews.

6.1.2. Crossref integration: Integrate with Crossref for automated DOI registration and citation linking.

6.2. Customizable forms and templates

6.2.1. Flexible form designers: Visually design and customize submission forms, review forms, and other data input forms.

6.2.2. Template libraries: Provide libraries of pre-designed templates for common use cases.

6.3. Branding and customization

6.3.1. Interface customization: Customize the platform's appearance and branding to align with journal or publisher identities.

6.3.2. Custom domain support: Host the platform on a custom domain. 

7\. Additional features

7.1. LMS integration

7.1.1. Learning management system integration: Integrate with platforms like Canvas to facilitate educational peer review processes.

7.1.2. Gradebook synchronization: Synchronize grades and feedback from peer reviews with the LMS gradebook.

7.2. Accessibility and mobile responsiveness

7.2.1. Accessibility standards adherence: Ensure compliance with accessibility guidelines (e.g., WCAG) to make the platform usable for individuals with disabilities.

7.2.2. Responsive design: Optimize the user interface for seamless use across various devices (e.g., desktops, tablets, mobile phones). 



6. Application: aieou.org

6.1 Concept

aieou.org is conceived as a Layer 5 domain module for the Meta Modal Platform (oMMP), serving as a publishing and archival platform that enforces full-context submission of research materials. In contrast to conventional journals that prioritize concise, polished narratives, aieou.org requires the inclusion of all relevant artifacts generated during the research process — whether ultimately used in the final analysis or not. This aligns with emerging reproducibility mandates in open science, which emphasize the value of sharing null results, exploratory models, and intermediate datasets (Munafò et al., 2017).OMMP\_framework.thesis



6.2 Features



Mandatory Full-Context Submission

All research material, including failed trials, calibration data, and exploratory notes, must accompany the primary submission. This preserves un space as defined in oMMP, ensuring that no observer-linked variables are lost.



Searchable Index of un Research

A dedicated search engine indexes both “used” and “unused” research materials. Researchers can search by domain, methodology, or observer ID, allowing connections between seemingly unrelated projects.



Structured Reviewer Options

Reviewers can:

  o Credit the work as relevant,

  o Mark it as not relevant (without removal), or

  o Provide structured critique for archival with the submission.

This process mirrors best practices in transparent peer review (Ross-Hellauer, 2017).



AI Usage Logging

All AI-assisted contributions are logged in a controlled research environment, ensuring reproducibility and compliance with emerging guidelines on AI in research (Nature Editorial, 2023).OMMP\_framework.thesis



6.3 Role in Closing the un Space Gap

By enforcing comprehensive submission and preservation of the observer’s entire research path, aieou.org functions as an observer-preserving publishing layer. This directly addresses the innovation shadow zone described in Section 5.2, preventing the silent loss of epistemically valuable material.

Such a system would also enable cross-domain serendipity: a dataset deemed irrelevant in one field might hold the key to a breakthrough in another. In this way, aieou.org extends oMMP’s reach beyond experimental science into the broader academic ecosystem, transforming the un space from an inaccessible void into a searchable, interconnected knowledge layer.OMMP\_framework.thesis



10.3 Development of aieou.org as a Formal Publishing Platform

Beyond its role as a Layer 5 oMMP module, aieou.org could evolve into a global open science repository with advanced un space search capabilities. By allowing research institutions, governments, and independent researchers to submit both used and unused data under a unified metadata schema, aieou.org could become a central node in the global research network. Integration with entropy trace mapping tools could make it the first publishing platform to quantify the completeness of preserved observational context.OMMP\_framework.thesis



6\. Application: aieou.org

6.1 Concept

aieou.org is conceived as a Layer 5 domain module for the Meta Modal Platform (oMMP), serving as a publishing and archival platform that enforces full-context submission of research materials. In contrast to conventional journals that prioritize concise, polished narratives, aieou.org requires the inclusion of all relevant artifacts generated during the research process — whether ultimately used in the final analysis or not. This aligns with emerging reproducibility mandates in open science, which emphasize the value of sharing null results, exploratory models, and intermediate datasets (Munafò et al., 2017).OMMP\_framework.thesis



6.2 Features



Mandatory Full-Context Submission

All research material, including failed trials, calibration data, and exploratory notes, must accompany the primary submission. This preserves un space as defined in oMMP, ensuring that no observer-linked variables are lost.



Searchable Index of un Research

A dedicated search engine indexes both “used” and “unused” research materials. Researchers can search by domain, methodology, or observer ID, allowing connections between seemingly unrelated projects.



Structured Reviewer Options

Reviewers can:

  o Credit the work as relevant,

  o Mark it as not relevant (without removal), or

  o Provide structured critique for archival with the submission.

This process mirrors best practices in transparent peer review (Ross-Hellauer, 2017).



AI Usage Logging

All AI-assisted contributions are logged in a controlled research environment, ensuring reproducibility and compliance with emerging guidelines on AI in research (Nature Editorial, 2023).OMMP\_framework.thesis



6.3 Role in Closing the un Space Gap

By enforcing comprehensive submission and preservation of the observer’s entire research path, aieou.org functions as an observer-preserving publishing layer. This directly addresses the innovation shadow zone described in Section 5.2, preventing the silent loss of epistemically valuable material.

Such a system would also enable cross-domain serendipity: a dataset deemed irrelevant in one field might hold the key to a breakthrough in another. In this way, aieou.org extends oMMP’s reach beyond experimental science into the broader academic ecosystem, transforming the un space from an inaccessible void into a searchable, interconnected knowledge layer.OMMP\_framework.thesis



10.3 Development of aieou.org as a Formal Publishing Platform

Beyond its role as a Layer 5 oMMP module, aieou.org could evolve into a global open science repository with advanced un space search capabilities. By allowing research institutions, governments, and independent researchers to submit both used and unused data under a unified metadata schema, aieou.org could become a central node in the global research network. Integration with entropy trace mapping tools could make it the first publishing platform to quantify the completeness of preserved observational context.OMMP\_framework.thesis



Proposed Research Endpoints for aieou.org (Layer 5 OMMP)



/submit — Endpoint for authenticated observer submissions (supports full-context bundle: primary data, unused data, calibration logs, AI contributions).



/review — Structured reviewer interface allowing “credit,” “not relevant,” or “critique” actions; all actions archived without deletion.



/search — Query index for “used” and “unused” research; supports domain, method, and observer-ID filters.



/trace/entropy — Generates Entropy Trace Maps (ETMs) to visualize ESR metric compliance across a submission’s lifecycle.



/dataset/link — Cross-links datasets that share observer IDs, Meta tokens, or Modal codes.



/ai/log — Returns AI-assist logs for a given submission, ensuring compliance with AI usage transparency requirements.



/export/context — Exports preserved un space context for integration with other OMMP-compliant archives.



/register/observer — Registers cryptographic observer identities (Ed25519 PKI) for attribution and reproducibility.



If you want, I can also merge these endpoints into a full Layer 5 OMMP spec section so they’re embedded directly into the framework’s normative architecture. That way, aieou isn’t just a module note — it becomes a fully formalized part of OMMP’s operational layer. Would you like me to do that?


/submit — Endpoint for authenticated observer submissions (supports full-context bundle: primary data, unused data, calibration logs, AI contributions).



/review — Structured reviewer interface allowing “credit,” “not relevant,” or “critique” actions; all actions archived without deletion.



/search — Query index for “used” and “unused” research; supports domain, method, and observer-ID filters.



/trace/entropy — Generates Entropy Trace Maps (ETMs) to visualize ESR metric compliance across a submission’s lifecycle.



/dataset/link — Cross-links datasets that share observer IDs, Meta tokens, or Modal codes.



/ai/log — Returns AI-assist logs for a given submission, ensuring compliance with AI usage transparency requirements.



/export/context — Exports preserved un space context for integration with other OMMP-compliant archives.



/register/observer — Registers cryptographic observer identities (Ed25519 PKI) for attribution and reproducibility.



Added Research Discovery \& Collaboration Endpoints



/research/open — Marks specific datasets, hypotheses, or methods as open for collaboration. Includes optional tags:



interest\_level (high/medium/low)



collaboration\_type (co-author, data-sharing, peer review, funding partner)



notes (free-text intent statement).



/research/seek — Allows an observer to declare a research need (equipment, domain expertise, analysis partner, funding, etc.).



/ideas/discover — Returns a list of emerging research ideas from unused datasets and exploratory notes in the archive, ranked by entropy-novelty metrics.



/ideas/subscribe — Push or pull feed of new high-entropy ideas in a user-selected domain, filtered by ESR scores.



/collaboration/match — Suggests possible collaborators based on:



Shared Meta tokens (physical context)



Overlapping Modal codes (phenomenon structure/function)



Observer skill tags and prior work history.



/trend/insight — Aggregates and surfaces trending underexplored topics across the archive, based on search queries and open research declarations.



/gap/map — Generates visual GitGap-style maps of un space regions where no research has been done, but related data exist in unused archives.

