# High-Level Requirements Document

**Version: 1.0**

## Introduction

### 1.1 Purpose

The purpose of this document is to outline the high-level requirements for the Generative AI Microservice. This microservice interprets the free text a person writes when they ask for help, and produces structured and generated output that the platform and its volunteers can act on.

### 1.2 Scope

The microservice is a set of AWS Lambda functions deployed from a single package and exposed through API Gateway under the `v1/genai` base path. It is invoked by the web client while a help request is being created and from the Request Details page, and by the Data and ML microservice for organisation search.

It is not on the critical path of a help request. The Request microservice owns the request lifecycle; Generative AI enriches it.

### 1.3 Related Documents

- [Requirements of Gen AI](https://github.com/saayam-for-all/ai/wiki/Requirements-of-Gen-AI), on this wiki, which carries the originating P0 and P1 requirements
- [Generative AI Life Cycle](https://github.com/saayam-for-all/ai/wiki/Generative-AI-life-cycle), on this wiki, which records the approach taken during the 2024 planning phase
- [GenAI Services Specification](https://github.com/saayam-for-all/ai/wiki/GenAI-Services-Specification), on this wiki, which specifies inputs, outputs, and runtime dependencies for each service
- [GenAI Cost Model](https://github.com/saayam-for-all/ai/wiki/GenAI-Cost-Model) ([in-repo spec](https://github.com/saayam-for-all/ai/blob/dev/docs/metrics/GENAI_COST_MODEL.md)), on this wiki, which records our measured token baseline, current spend, volume forecasts, and free-tier limits
- [The Use Cases document](https://github.com/saayam-for-all/docs/wiki/Use-Cases) in the Docs repository wiki
- *Help Request Categories For 1.0 MVP* and *1.0 MVP Help Categories Use Cases*, maintained by the Business Analysis team

### 1.4 Requirement Traceability

Two requirements were recorded at the outset. Their current status is as follows.

| ID | Requirement | Status |
| --- | --- | --- |
| `Gen_Text_For_Volunteer` (P1) | A volunteer may request further information about a request from the request drill down page | Implemented, as Generate Answer, reached from More Information on the Request Details page |
| `Gen_Text_When_No_Volunteer` (P0) | Where no volunteer matches a help request, generate a text response in the language the request was submitted in | Partially implemented. The generation capability exists as Generate Answer, but it is invoked by a person choosing More Information, not automatically on a failure to match a volunteer. The automatic trigger is not built |

Four of the five services now in production, covering category prediction, subject generation, organisation search and emergency contacts, have no entry in the original requirements. Their requirements are stated in this document and in [GenAI Services Specification](https://github.com/saayam-for-all/ai/wiki/GenAI-Services-Specification), and [Requirements of Gen AI](https://github.com/saayam-for-all/ai/wiki/Requirements-of-Gen-AI) needs extending to match.

## Functional Requirements

### 2.1 Category Prediction

- Accept a free text description and return ranked help categories with a confidence score and the full hierarchy path.
- Classify against the help taxonomy defined by the Business Analysis team.
- Support the twelve languages offered by the help request form.
- Return an empty result rather than a guess when no category can be determined.

### 2.2 Subject Generation

- Produce a short subject line from a request description, within a fixed length limit.
- Preserve details stated by the requester and introduce none that were not.
- Read as the person's own concern rather than as a diagnosis or an instruction.

### 2.3 Answer Generation

- Generate guidance for a help request, personalised by category, location, gender and age where supplied.
- Support multi-turn follow-up questions, answering the pending question rather than restating the original request.
- Answer from the request text supplied by the caller where possible, treating the request store as a source rather than a precondition.
- Reject any turn in a supplied transcript that claims the system role.

### 2.4 Organisation Search

- Return six organisations relevant to a request, three non-profit and three for-profit.
- Return every field in the agreed contract on every organisation, so that consumers receive a complete record.
- Degrade to a secondary provider when the primary is unavailable, and report a provider outage distinctly from an empty result.

### 2.5 Emergency Contacts

- Resolve a location to a country and return the emergency numbers for that country.
- Resolve strictly within the requested country. Where a specific service is unavailable, fall back to that country's own general emergency line and flag it as a fallback.
- Return no number rather than another jurisdiction's number.
- Return numbers in a dialable form, together with a display form in the requested language's numerals.

### 2.6 Model Provider Management

- Retrieve provider credentials from AWS Systems Manager Parameter Store at runtime with decryption enabled.
- Use a primary model provider with an automatic fallback to a secondary provider.
- Constrain structured output so that responses can be consumed by code.

### 2.7 Logging and Monitoring

- Record the shape of each request payload, never its content, so that health, housing and financial detail does not enter logs.
- Account for token usage across every model call in a request, monitoring spend and rate limits as documented in [GenAI Cost Model](https://github.com/saayam-for-all/ai/wiki/GenAI-Cost-Model).
- Return errors that distinguish a client fault, a provider outage, an unavailable data store and a schema mismatch.

## Non-Functional Requirements

### 3.1 Performance

Category prediction and subject generation are invoked while a person is filling in a form, so response time is user facing and must remain within a few seconds.

### 3.2 Scalability

Each service is deployed as an independent Lambda function so that load on one does not affect the others, and so that memory and timeout can be tuned per service.

### 3.3 Reliability

- A failure in one service must not affect the others. Dependencies specific to a single service are imported lazily.
- A failure of a model provider must degrade the result rather than fail the request.
- A failure must never be returned in the shape of a successful answer.

### 3.4 Security

- Credentials are held in Parameter Store and never in source or in function configuration.
- All endpoints are authenticated through Cognito.
- Error responses returned to callers must not contain provider or driver detail.

### 3.5 Compliance

- Database access is read only and limited to the request tables required to answer.
- Emergency information is served from a versioned dataset with a recorded source for every number, and is never generated at request time.

### 3.6 Internationalisation

The platform accepts help requests in twelve languages, and generated output is read by the person who submitted the request. Every service shall therefore operate in the language the request was submitted in rather than translating into English first, and shall return output in that same language.

Classification meets this requirement. Subject generation does not yet do so consistently, and the language of its output is currently determined by the model rather than specified.

## Future Scope

The following are recorded intentions, not current behaviour.

| Item | Note |
| --- | --- |
| Voice input and voice output | Stated from the outset. Requests are accepted as text and responses returned as text today. Voice would sit in front of the existing services rather than replace them |
| Grounding generated output in served request history | Stated from the outset. No service reads historical served requests today |
| Grounding organisation results in a verified dataset | Organisation results are generated rather than looked up. Until this is closed, results are not to be presented as verified contact details |
| Automatic invocation when no volunteer is matched | The trigger described by `Gen_Text_When_No_Volunteer` |
