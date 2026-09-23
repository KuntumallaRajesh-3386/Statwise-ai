import { useEffect, useState } from "react";
import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

export default function AssessmentStudio({
  initialTopic
}) {
  // --------------------------------
  // State
  // --------------------------------

  const [file, setFile] = useState(null);
  const [document, setDocument] = useState(null);

  const [topic, setTopic] = useState("Sampling");
  useEffect(() => {

  if (!initialTopic) {
    return;
  }

  setTopic(initialTopic);

  setQuestions([]);
  setCurrentQuestion(0);
  setSelectedAnswer(null);
  setSubmitted(false);
  setScore(0);
  setAssessmentResult(null);

}, [initialTopic]);

  const [questions, setQuestions] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);

  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  const [score, setScore] = useState(0);

  const [loading, setLoading] = useState(false);

  const [assessmentResult, setAssessmentResult] = useState(null);

  // --------------------------------
  // Upload PDF
  // --------------------------------

  const uploadDocument = async () => {
    if (!file) {
      alert("Please select a PDF first.");
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();

      formData.append("file", file);

      const response = await axios.post(
        `${API_URL}/documents/upload`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data"
          }
        }
      );

      if (response.data.error) {
        alert(response.data.error);
        return;
      }

      setDocument(response.data);

      // Reset quiz state
      setQuestions([]);
      setCurrentQuestion(0);
      setSelectedAnswer(null);
      setSubmitted(false);
      setScore(0);
      setAssessmentResult(null);

      alert("Document processed successfully.");

    } catch (error) {
      console.error("Upload error:", error);

      const message =
        error.response?.data?.detail ||
        error.response?.data?.error ||
        "Failed to process document.";

      alert(message);

    } finally {
      setLoading(false);
    }
  };

 

  // --------------------------------
  // Generate AI Quiz
  // --------------------------------

  const generateQuiz = async () => {
    if (!document) {
      alert("Please upload and process a PDF first.");
      return;
    }

    setLoading(true);

    try {
      const response = await axios.get(
        `${API_URL}/mcqs?topic=${encodeURIComponent(topic)}`
      );

      if (response.data.error) {
        alert(response.data.error);
        setQuestions([]);
        return;
      }

      const generatedQuestions = Array.isArray(
        response.data.questions
      )
        ? response.data.questions
        : [];

      if (generatedQuestions.length === 0) {
        alert(
          "No questions were generated from the document."
        );

        setQuestions([]);
        return;
      }

      setQuestions(generatedQuestions);
      setCurrentQuestion(0);
      setSelectedAnswer(null);
      setSubmitted(false);
      setScore(0);

      // Clear previous competency result
      setAssessmentResult(null);

    } catch (error) {
      console.error(
        "Quiz generation error:",
        error
      );

      const message =
        error.response?.data?.detail ||
        error.response?.data?.error ||
        "Failed to generate quiz.";

      alert(message);

      setQuestions([]);

    } finally {
      setLoading(false);
    }
  };

  // --------------------------------
  // Submit Answer
  // --------------------------------

  const submitAnswer = () => {
    if (selectedAnswer === null) {
      alert("Please select an answer.");
      return;
    }

    const question = questions[currentQuestion];

    if (!question) {
      return;
    }

    const isCorrect =
      selectedAnswer === question.answer;

    if (isCorrect) {
      setScore(
        (previousScore) =>
          previousScore + 1
      );
    }

    setSubmitted(true);
  };

  // --------------------------------
  // Calculate Final Competency Result
  // --------------------------------

  const calculateFinalResult = async () => {
    if (questions.length === 0) {
      alert("No assessment questions found.");
      return;
    }
    

    try {
      // --------------------------------
      // 1. Get current saved competency
      // --------------------------------

      const competencyResponse = await axios.get(
        `${API_URL}/competency/${encodeURIComponent(topic)}`
      );

      const savedLevel =
        competencyResponse.data?.level;

      const initialLevel =
        savedLevel !== null &&
        savedLevel !== undefined
          ? Number(savedLevel)
          : 2;

      console.log(
        "Current saved competency:",
        {
          topic,
          level: initialLevel
        }
      );

      // --------------------------------
      // 2. Calculate adaptive result
      // --------------------------------

      const response = await axios.post(
        `${API_URL}/adaptive/result`,
        {
          topic: topic,
          correct_answers: score,
          total_questions: questions.length,
          initial_level: initialLevel
        }
      );

      console.log(
        "Adaptive result:",
        response.data
      );

      // Show result in UI
      setAssessmentResult(response.data);

      // --------------------------------
      // 3. Update saved competency
      // --------------------------------

      console.log(
        "Updating competency:",
        {
          topic: response.data.topic,
          level: response.data.final_level,
          score: response.data.score
        }
      );

     const updateResponse = await axios.post(
      `${API_URL}/competency/update`,
      {
        topic: response.data.topic,
        level: response.data.final_level,
        assessment_score: response.data.score
      }
    );

      console.log(
        "Competency update response:",
        updateResponse.data
      );

      // --------------------------------
      // 4. Notify Dashboard
      // --------------------------------

      window.dispatchEvent(
        new Event("competencyUpdated", {
            detail: response.data
        })
      );

      console.log(
        "Dashboard refresh event dispatched."
      );

      // --------------------------------
      // 5. Success message
      // --------------------------------

      console.log(
        "Competency successfully updated."
      );

    } catch (error) {
      console.error(
        "Assessment result error:",
        error
      );

      const message =
        error.response?.data?.detail ||
        error.response?.data?.error ||
        "Could not calculate competency result.";

      alert(message);
    }
  };

  // --------------------------------
  // Next Question
  // --------------------------------

  const nextQuestion = () => {
    if (
      currentQuestion <
      questions.length - 1
    ) {
      setCurrentQuestion(
        (previous) =>
          previous + 1
      );

      setSelectedAnswer(null);
      setSubmitted(false);
    }
  };

  

  // --------------------------------
  // Change Topic
  // --------------------------------

  const handleTopicChange = (event) => {
    const newTopic = event.target.value;

    setTopic(newTopic);

    setQuestions([]);
    setCurrentQuestion(0);
    setSelectedAnswer(null);
    setSubmitted(false);
    setScore(0);
    setAssessmentResult(null);
  };

  // --------------------------------
  // Select New File
  // --------------------------------

  const handleFileChange = (event) => {
    const selectedFile =
      event.target.files?.[0] || null;

    setFile(selectedFile);
    setDocument(null);
    setQuestions([]);
    setCurrentQuestion(0);
    setSelectedAnswer(null);
    setSubmitted(false);
    setScore(0);
    setAssessmentResult(null);
  };

  // --------------------------------
  // Current Question
  // --------------------------------

  const question =
    Array.isArray(questions) &&
    questions.length > 0 &&
    currentQuestion >= 0 &&
    currentQuestion < questions.length
      ? questions[currentQuestion]
      : null;

  // --------------------------------
  // UI
  // --------------------------------

  return (
    <div className="studio">

      {/* --------------------------------
          Header
      -------------------------------- */}

      <div className="studio-header">

        <div>

          <span className="studio-badge">
            AI ASSESSMENT STUDIO
          </span>

          <h1>
            Learning Material Assessment
          </h1>

          <p>
            Upload official learning material
            and generate document-grounded
            assessment questions.
          </p>

        </div>

      </div>


      {/* --------------------------------
          Upload Card
      -------------------------------- */}

      <div className="studio-card">

        <h2>
          1. Upload Learning Material
        </h2>

        <p>
          Upload a PDF containing the
          learning material from which
          the assessment will be generated.
        </p>

        <div className="upload-area">

          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
          />

          {file && (

            <div className="document-info">

              <strong>
                {file.name}
              </strong>

              <span>
                {(
                  file.size /
                  1024 /
                  1024
                ).toFixed(2)}{" "}
                MB
              </span>

            </div>

          )}

          <button
            className="primary-button"
            onClick={uploadDocument}
            disabled={!file || loading}
          >
            {loading
              ? "Processing..."
              : "Process Material"}
          </button>

        </div>

      </div>


      {/* --------------------------------
          Document Result
      -------------------------------- */}

      {document && (

        <div className="studio-card">

          <h2>
            2. Material Processed
          </h2>

          <div className="document-info">

            <div>

              <strong>
                {document.filename}
              </strong>

              <p>
                Pages:{" "}
                {document.page_count ?? 0}
              </p>

              <p>
                Text chunks:{" "}
                {document.chunk_count ?? 0}
              </p>

            </div>

          </div>


          {/* Topic Selection */}

          <div className="quiz-settings">

            <label>
              Assessment Topic
            </label>

            <select
              value={topic}
              onChange={handleTopicChange}
            >

              <option value="Sampling">
                Sampling
              </option>

              <option value="Statistical Methods">
                Statistical Methods
              </option>

              <option value="Python">
                Python
              </option>

              <option value="SQL">
                SQL
              </option>

              <option value="Data Visualization">
                Data Visualization
              </option>

            </select>

          </div>


          {/* Generate Quiz */}

          <button
            className="primary-button"
            onClick={generateQuiz}
            disabled={loading}
          >
            {loading
              ? "Generating AI Quiz..."
              : "Generate AI Quiz"}
          </button>

        </div>

      )}


      {/* --------------------------------
          Quiz
      -------------------------------- */}

      {question &&
        Array.isArray(question.options) &&
        question.options.length > 0 && (

          <div className="studio-card quiz-card">

            {/* Question Progress */}

            <div className="question-progress">

              Question{" "}
              {currentQuestion + 1}{" "}
              of{" "}
              {questions.length}

            </div>


            {/* Question */}

            <h2>
              {question.question}
            </h2>


            {/* Difficulty */}

            {question.difficulty && (

              <div className="difficulty">

                Difficulty:{" "}

                <strong>
                  {question.difficulty}
                </strong>

              </div>

            )}


            {/* Options */}

            <div className="options">

              {question.options.map(
                (option, index) => (

                  <button
                    key={`${currentQuestion}-${index}`}
                    className={`option ${
                      selectedAnswer === index
                        ? "selected"
                        : ""
                    }`}
                    onClick={() => {

                      if (!submitted) {

                        setSelectedAnswer(
                          index
                        );

                      }

                    }}
                    disabled={submitted}
                  >

                    <span>
                      {String.fromCharCode(
                        65 + index
                      )}
                      .
                    </span>{" "}

                    {option}

                  </button>

                )
              )}

            </div>


            {/* Submit Answer */}

            {!submitted && (

              <button
                className="primary-button"
                onClick={submitAnswer}
                disabled={
                  selectedAnswer === null
                }
              >
                Submit Answer
              </button>

            )}


            {/* Feedback */}

            {submitted && (

              <div className="feedback">

                {selectedAnswer ===
                question.answer ? (

                  <div className="correct-feedback">

                    <strong>
                      Correct!
                    </strong>

                    <p>
                      Your answer is
                      correct.
                    </p>

                  </div>

                ) : (

                  <div className="incorrect-feedback">

                    <strong>
                      Incorrect
                    </strong>

                    <p>
                      The correct answer is:
                    </p>

                    <p>

                      <strong>

                        {
                          question.options[
                            question.answer
                          ] ??
                          "Unavailable"
                        }

                      </strong>

                    </p>

                  </div>

                )}


                {/* Explanation */}

                {question.explanation && (

                  <div className="explanation">

                    <strong>
                      Explanation
                    </strong>

                    <p>
                      {question.explanation}
                    </p>

                  </div>

                )}


                {/* Evidence */}

                {question.evidence && (

                  <div className="evidence">

                    <strong>
                      Source Evidence
                    </strong>

                    <p>
                      {question.evidence}
                    </p>

                  </div>

                )}


                {/* Source Page */}

                {question.source_page && (

                  <div className="source-page">

                    Source page:{" "}

                    <strong>
                      {question.source_page}
                    </strong>

                  </div>

                )}


                {/* --------------------------------
                    Next Question / Finish
                -------------------------------- */}

                {currentQuestion <
                questions.length - 1 ? (

                  <button
                    className="primary-button"
                    onClick={nextQuestion}
                  >
                    Next Question
                  </button>

                ) : (

                  <div className="quiz-complete">

                    <h2>
                      Assessment Complete
                    </h2>

                    <p>
                      Score:{" "}
                      <strong>
                        {score} / {questions.length}
                      </strong>
                    </p>

                    <p>
                      Your assessment has been
                      completed successfully.
                    </p>


                    {!assessmentResult && (

                      <button
                        type="button"
                        className="primary-button"
                        onClick={
                          calculateFinalResult
                        }
                        style={{
                          display: "block",
                          visibility: "visible",
                          opacity: 1,
                          marginTop: "20px"
                        }}
                      >
                        Calculate Competency Result
                      </button>

                    )}


                    {assessmentResult && (

                      <div className="assessment-result">

                        <h2>
                          Competency Result
                        </h2>

                        <div className="result-grid">

                          <div>

                            <span>
                              Topic
                            </span>

                            <strong>
                              {assessmentResult.topic}
                            </strong>

                          </div>


                          <div>

                            <span>
                              Score
                            </span>

                            <strong>
                              {assessmentResult.score}%
                            </strong>

                          </div>


                          <div>

                            <span>
                              Before
                            </span>

                            <strong>
                              {assessmentResult.initial_level}/5
                            </strong>

                          </div>


                          <div>

                            <span>
                              After
                            </span>

                            <strong>
                              {assessmentResult.final_level}/5
                            </strong>

                          </div>


                          <div>

                            <span>
                              Improvement
                            </span>

                            <strong>
                              {assessmentResult.improvement >= 0
                                ? "+"
                                : ""}
                              {assessmentResult.improvement}
                            </strong>

                          </div>

                        </div>

                      </div>

                    )}

                  </div>

                )}

              </div>

            )}

          </div>

        )}


      {/* --------------------------------
          Empty State
      -------------------------------- */}

      {!question &&
        document &&
        questions.length === 0 && (

          <div className="studio-card">

            <h2>
              Ready to Generate Assessment
            </h2>

            <p>
              Select a competency topic
              and click "Generate AI Quiz".
            </p>

          </div>

        )}

    </div>
  );
}