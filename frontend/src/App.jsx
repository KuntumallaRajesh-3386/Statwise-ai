import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";
import AssessmentStudio from "./pages/AssessmentStudio";

const API_URL = "http://127.0.0.1:8000";

const DEFAULT_COMPETENCIES = {
  "Statistical Methods": 3,
  Sampling: 3,
  Python: 3,
  SQL: 3,
  "Data Visualization": 3,
  GIS: 3,
  "AI and Machine Learning": 3,
  Cybersecurity: 3,
  Leadership: 3,
  Communication: 3,
};

function App() {
  const [page, setPage] = useState("dashboard");
  const [reassessmentTopic, setReassessmentTopic] =
  useState(null);

  const [role, setRole] = useState("Statistical Officer");

  const [scores, setScores] = useState(
    DEFAULT_COMPETENCIES
  );

  const [result, setResult] = useState(null);

  const [recommendations, setRecommendations] = useState([]);

  const [history, setHistory] = useState([]);

  const [historyTopic, setHistoryTopic] =
    useState("All");

  const [loading, setLoading] = useState(false);
  // Competency improvement history
const [improvementHistory, setImprovementHistory] =
  useState(() => {
    try {
      return JSON.parse(
        localStorage.getItem(
          "statwiseImprovementHistory"
        ) || "[]"
      );
    } catch {
      return [];
    }
  });
  const [learningProgress, setLearningProgress] = useState(() => {
  try {
    return JSON.parse(
      localStorage.getItem("statwiseLearningProgress") || "{}"
    );
  } catch {
    return {};
  }
});
// --------------------------------
// Learning Progress Tracking
// --------------------------------

const updateLearningStatus = (
  competency,
  status
) => {
  const updatedProgress = {
    ...learningProgress,
    [competency]: status
  };

  setLearningProgress(updatedProgress);

  localStorage.setItem(
    "statwiseLearningProgress",
    JSON.stringify(updatedProgress)
  );
};

  // --------------------------------
  // Load saved competencies
  // --------------------------------

  const loadSavedCompetencies = async () => {
    try {
      const response = await axios.get(
        `${API_URL}/competencies`
      );

      const saved =
        response.data?.competencies || {};

      setScores((previousScores) => ({
        ...previousScores,
        ...saved,
      }));
    } catch (error) {
      console.error(
        "Could not load saved competencies:",
        error
      );
    }
  };

  // --------------------------------
  // Load assessment history
  // --------------------------------

  const loadAssessmentHistory = async () => {
    try {
      const response = await axios.get(
        `${API_URL}/competency-history`
      );

      const backendHistory =
        response.data?.history || [];

      setHistory(backendHistory);

      const formattedImprovementHistory =
        backendHistory.map((item, index) => ({
          id:
            item.id ||
            `${item.topic}-${item.assessed_at}-${index}`,
          topic: item.topic,
          initial_level: Number(
            item.previous_level ?? 0
          ),
          final_level: Number(
            item.new_level ?? 0
          ),
          improvement:
            Number(item.new_level ?? 0) -
            Number(item.previous_level ?? 0),
          score: Number(
            item.assessment_score ?? 0
          ),
          date:
            item.assessed_at ||
            new Date().toISOString()
        }));

      setImprovementHistory(
        formattedImprovementHistory
      );

      localStorage.setItem(
        "statwiseImprovementHistory",
        JSON.stringify(
          formattedImprovementHistory
        )
      );
    } catch (error) {
      console.error(
        "Could not load assessment history:",
        error
      );
    }
  };

  // --------------------------------
  // Refresh dashboard analysis
  // --------------------------------

  const refreshDashboardAnalysis = async (
    currentScores
  ) => {
    try {
      setLoading(true);

      const assessmentResponse =
        await axios.post(
          `${API_URL}/assessment`,
          {
            role,
            scores: currentScores,
          }
        );

      setResult(
        assessmentResponse.data
      );

      const recommendationResponse =
        await axios.post(
          `${API_URL}/recommendations`,
          {
            role,
            competencies: currentScores,
          }
        );

      setRecommendations(
        recommendationResponse.data
          ?.recommendations || []
      );
    } catch (error) {
    console.error(
      "Assessment error:",
      error.response?.data || error
    );

    alert(
      JSON.stringify(
        error.response?.data || {
          message: error.message
        },
        null,
        2
      )
    );

  } finally {
    setLoading(false);
  }
};

  // --------------------------------
  // Refresh dashboard
  // --------------------------------

  const refreshDashboard = async () => {
    try {
      const response = await axios.get(
        `${API_URL}/competencies`
      );

      const saved =
        response.data?.competencies || {};

      const mergedScores = {
        ...DEFAULT_COMPETENCIES,
        ...scores,
        ...saved,
      };

      setScores(mergedScores);

      await refreshDashboardAnalysis(
        mergedScores
      );
    } catch (error) {
      console.error(
        "Could not refresh dashboard:",
        error
      );
    }
  };

  // --------------------------------
  // Initial load
  // --------------------------------

  useEffect(() => {
  loadSavedCompetencies();

  const handleCompetencyUpdated = () => {
    loadSavedCompetencies();
  };

  const handleAssessmentCompleted = () => {
    console.log(
      "assessmentCompleted event received."
    );

    setTimeout(() => {
      loadAssessmentHistory();
    }, 300);
  };

  window.addEventListener(
    "competencyUpdated",
    handleCompetencyUpdated
  );

  window.addEventListener(
    "assessmentCompleted",
    handleAssessmentCompleted
  );

  return () => {
    window.removeEventListener(
      "competencyUpdated",
      handleCompetencyUpdated
    );

    window.removeEventListener(
      "assessmentCompleted",
      handleAssessmentCompleted
    );
  };
}, []);

  // --------------------------------
  // Dashboard page refresh
  // --------------------------------

  useEffect(() => {
    if (page === "dashboard") {
      refreshDashboard();
      loadAssessmentHistory();
    }
  }, [page]);

  // --------------------------------
  // Listen for competency updates
  // --------------------------------

  useEffect(() => {
    const handleCompetencyUpdated = () => {
      console.log(
        "competencyUpdated event received."
      );

      refreshDashboard();
      loadAssessmentHistory();
    };

    window.addEventListener(
      "competencyUpdated",
      handleCompetencyUpdated
    );

    return () => {
      window.removeEventListener(
        "competencyUpdated",
        handleCompetencyUpdated
      );
    };
  }, []);

  // --------------------------------
  // Manual competency update
  // --------------------------------

  const updateScore = (
    competency,
    value
  ) => {
    setScores((previousScores) => ({
      ...previousScores,
      [competency]: Number(value),
    }));
  };

  // --------------------------------
  // Submit dashboard assessment
  // --------------------------------
const submitAssessment = async () => {
  setLoading(true);

  try {
    const payload = {
      role: role,
      scores: scores
    };

    console.log(
      "FINAL /assessment PAYLOAD:",
      JSON.stringify(payload, null, 2)
    );

    const assessmentResponse = await axios.post(
      `${API_URL}/assessment`,
      payload
    );

    console.log(
      "ASSESSMENT RESPONSE:",
      assessmentResponse.data
    );

    const assessmentResult =
      assessmentResponse.data;

    setResult(assessmentResult);

    const recommendationResponse =
      await axios.post(
        `${API_URL}/recommendations`,
        {
          competencies:
            assessmentResult.competencies
        }
      );

    setRecommendations(
      recommendationResponse.data?.recommendations || []
    );

  } catch (error) {
    console.error(
      "ASSESSMENT ERROR:",
      error.response?.data || error
    );

    alert(
      JSON.stringify(
        error.response?.data || {
          message: error.message
        },
        null,
        2
      )
    );

  } finally {
    setLoading(false);
  }
};
  

  // --------------------------------
  // History topics
  // --------------------------------

  const historyTopics = [
    "All",
    ...Array.from(
      new Set(
        history.map(
          (item) => item.topic
        )
      )
    ),
  ];

  // --------------------------------
  // Filter history
  // --------------------------------

  const filteredHistory =
    historyTopic === "All"
      ? [...history].reverse()
      : history
          .filter(
            (item) =>
              item.topic === historyTopic
          )
          .reverse();

  // --------------------------------
  // Current competency for chart
  // --------------------------------

  const selectedHistory =
    historyTopic === "All"
      ? filteredHistory
      : filteredHistory;

  // --------------------------------
  // Dashboard
  // --------------------------------

  if (page === "dashboard") {
    return (
      <div className="app-shell">

        {/* NAVBAR */}

        <header className="topbar">
          <div className="brand">
            <div className="brand-mark">
              SW
            </div>

            <div>
              <h1>STATWISE AI</h1>
              <span>
                Competency Intelligence Platform
              </span>
            </div>
          </div>

          <nav>
            <button
              className="nav-button active"
              onClick={() =>
                setPage("dashboard")
              }
            >
              Dashboard
            </button>

            <button
              className="nav-button"
              onClick={() =>
                setPage("assessment")
              }
            >
              Assessment Studio
            </button>
          </nav>
        </header>

        {/* MAIN */}

        <main className="main-container">

          {/* HERO */}

          <section className="hero">
            <div>
              <span className="eyebrow">
                COMPETENCY INTELLIGENCE
              </span>

              <h2>
                Welcome back
              </h2>

              <p>
                Track your professional
                competency profile and identify
                the skills that need development.
              </p>
            </div>

            <div className="role-selector">
              <label>
                Professional Role
              </label>

              <select
                value={role}
                onChange={(event) =>
                  setRole(event.target.value)
                }
              >
                <option>
                  Statistical Officer
                </option>

                <option>
                  Data Analyst
                </option>
              </select>
            </div>
          </section>

          {/* COMPETENCY PROFILE */}

          <section className="card">

            <div className="section-heading">
              <div>
                <h2>
                  Competency Profile
                </h2>

                <p className="subtitle">
                  Your current competency
                  levels across key professional
                  areas.
                </p>
              </div>
            </div>

            <div className="competency-grid">

              {Object.entries(scores).map(
                ([competency, level]) => (
                  <div
                    className="competency-card"
                    key={competency}
                  >
                    <div className="competency-header">

                      <h3>
                        {competency}
                      </h3>

                      <span className="level-badge">
                        {level}/5
                      </span>

                    </div>

                    <div className="level-track">

                      {[1, 2, 3, 4, 5].map(
                        (levelValue) => (
                          <label
                            key={`${competency}-${levelValue}`}
                            className={
                              levelValue <= level
                                ? "level-dot active"
                                : "level-dot"
                            }
                          >
                            <input
                              type="radio"
                              name={`level-${competency}`}
                              value={levelValue}
                              checked={
                                level ===
                                levelValue
                              }
                              onChange={() =>
                                updateScore(
                                  competency,
                                  levelValue
                                )
                              }
                            />

                            <span>
                              {levelValue}
                            </span>
                          </label>
                        )
                      )}

                    </div>
                  </div>
                )
              )}

            </div>

            <div className="dashboard-actions">
              <button
                className="primary-button"
                onClick={
                  submitAssessment
                }
                disabled={loading}
              >
                {loading
                  ? "Analyzing..."
                  : "Analyze Competencies"}
              </button>
            </div>

          </section>

          {/* ANALYSIS */}

          {result && (
            <section className="card">

              <div className="section-heading">
                <div>
                  <h2>
                    Competency Analysis
                  </h2>

                  <p className="subtitle">
                    AI-assisted analysis of your
                    current competency profile.
                  </p>
                </div>
              </div>

              <div className="analysis-grid">

                <div className="analysis-card">
                  <span>
                    Overall Score
                  </span>

                  <strong>
  {result?.competencies?.length
    ? (
        result.competencies.reduce(
          (total, item) =>
            total + Number(item.current_level || 0),
          0
        ) / result.competencies.length
      ).toFixed(1) + "/5"
    : "—"}
</strong>
                </div>

                <div className="analysis-card">
                  <span>
                    Role
                  </span>

                  <strong>
                    {role}
                  </strong>
                </div>

                <div className="analysis-card">
                  <span>
                    Competencies
                  </span>

                  <strong>
                    {Object.keys(
                      scores
                    ).length}
                  </strong>
                </div>

              </div>

            </section>
          )}

          {/* GAP ANALYSIS */}

          {result?.gaps &&
            result.gaps.length > 0 && (
              <section className="card">

                <div className="section-heading">
                  <div>
                    <h2>
                      Competency Gaps
                    </h2>

                    <p className="subtitle">
                      Areas where additional
                      development may be required.
                    </p>
                  </div>
                </div>

                <div className="recommendation-list">

                  {result.gaps.map(
                    (item) => (
                      <div
                        className="course-card"
                        key={`${item.topic}-${item.required_level}`}
                      >

                        <div className="course-number">
                          !
                        </div>

                        <div className="course-content">

                          <div className="course-top">

                            <div>
                              <h3>
                                {item.topic}
                              </h3>

                              <span className="provider">
                                Competency Gap
                              </span>
                            </div>

                            <div className="match">
                              <strong>
                                {item.current_level}/5
                              </strong>

                              <span>
                                Current
                              </span>
                            </div>

                          </div>

                          <div className="course-info">

                            <span>
                              Current:{" "}
                              {item.current_level}/5
                            </span>

                            <span>
                              Required:{" "}
                              {item.required_level}/5
                            </span>

                            <span>
                              Gap:{" "}
                              {item.gap}
                            </span>

                          </div>

                        </div>

                      </div>
                    )
                  )}

                </div>

              </section>
            )}
            {/* =========================================
    PERSONALIZED LEARNING PATH
========================================= */}

{result?.competencies?.length > 0 && (

  <section className="card">

    <div className="section-heading">

      <div>
        <h2>🎯 Personalized Learning Path</h2>

        <p className="subtitle">
          A step-by-step development path based
          on your competency gaps.
        </p>
      </div>

    </div>
    {/* LEARNING PATH SUMMARY */}

<div className="learning-summary">

  <div className="learning-summary-item">

    <span className="learning-summary-label">
      Competencies to Develop
    </span>

    <strong>
      {
        result.competencies.filter((item) => {
          const current =
            Number(item.current_level) || 0;

          const required =
            Number(item.required_level) || 0;

          return required > current;
        }).length
      }
    </strong>

  </div>

  <div className="learning-summary-item">

    <span className="learning-summary-label">
      High Priority
    </span>

    <strong>
      {
        result.competencies.filter((item) => {
          const current =
            Number(item.current_level) || 0;

          const required =
            Number(item.required_level) || 0;

          return required - current >= 2;
        }).length
      }
    </strong>

  </div>

  <div className="learning-summary-item">

    <span className="learning-summary-label">
      Medium Priority
    </span>

    <strong>
      {
        result.competencies.filter((item) => {
          const current =
            Number(item.current_level) || 0;

          const required =
            Number(item.required_level) || 0;

          const gap = required - current;

          return gap === 1;
        }).length
      }
    </strong>

  </div>

</div>
    <div className="learning-path">

      {result.competencies
        .map((item) => {

          const currentLevel =
            Number(item.current_level) || 0;

          const requiredLevel =
            Number(item.required_level) || 0;

          const gap =
            Math.max(
              0,
              requiredLevel - currentLevel
            );

          return {
            ...item,
            calculatedGap: gap,
          };

        })

        .filter(
          (item) => item.calculatedGap > 0
        )

        .sort(
          (a, b) =>
            b.calculatedGap -
            a.calculatedGap
        )

        .map((item, index) => {
          const learningStatus =
  learningProgress[item.competency] ||
  "Not Started";

          const relatedCourses =
            recommendations.filter(
              (course) =>
                String(
                  course.competency || ""
                ).toLowerCase() ===
                String(
                  item.competency || ""
                ).toLowerCase()
            );

          const priority =
            item.calculatedGap >= 2
              ? "High Priority"
              : "Medium Priority";

          const progress =
            item.required_level > 0
              ? Math.min(
                  100,
                  (
                    item.current_level /
                    item.required_level
                  ) * 100
                )
              : 0;

          return (

            <div
              className="learning-step"
              key={item.topic}
            >

              <div className="learning-step-number">
                {index + 1}
              </div>

              <div className="learning-step-content">

                <div className="learning-step-header">
                   <div className="learning-status">

  <span className="learning-status-label">
    Learning Status
  </span>

  <select
    value={learningStatus}
    onChange={(e) =>
      updateLearningStatus(
        item.competency,
        e.target.value
      )
    }
  >

    <option value="Not Started">
      Not Started
    </option>

    <option value="In Progress">
      In Progress
    </option>

    <option value="Completed">
      Completed
    </option>

  </select>

</div>

                  <div>

                    <span className="learning-label">
                      LEARNING STEP
                    </span>

                    <h3>
                      {item.topic}
                    </h3>

                  </div>

                  <span
                    className={
                      priority === "High Priority"
                        ? "priority-badge high-priority"
                        : "priority-badge medium-priority"
                    }
                  >
                    {priority}
                  </span>

                </div>

                <div className="learning-levels">

                  <div className="learning-level">

                    <span>
                      Current Level
                    </span>

                    <strong>
                      {item.current_level}/5
                    </strong>

                  </div>

                  <div className="learning-arrow">
                    →
                  </div>

                  <div className="learning-level">

                    <span>
                      Required Level
                    </span>

                    <strong>
                      {item.required_level}/5
                    </strong>

                  </div>

                  <div className="learning-level gap-value">

                    <span>
                      Development Gap
                    </span>

                    <strong>
                      {item.calculatedGap}
                    </strong>

                  </div>

                </div>

                <div className="learning-progress">

                  <div className="learning-progress-header">

                    <span>
                      Progress toward required level
                    </span>

                    <span>
                      {item.current_level}/
                      {item.required_level}
                    </span>

                  </div>

                  <div className="learning-progress-track">

                    <div
                      className="learning-progress-fill"
                      style={{
                        width: `${progress}%`
                      }}
                    />

                  </div>

                </div>

                {relatedCourses.length > 0 ? (

                  <div className="learning-resource">

                    <div className="resource-icon">
                      📚
                    </div>

                    <div className="resource-content">

                      <span>
                        Recommended Learning
                      </span>

                      <strong>
                        {relatedCourses[0].title}
                      </strong>

                      <small>
                        {relatedCourses[0].provider ||
                          "Recommended Learning"}
                      </small>

                    </div>

                  </div>

                ) : (

                  <div className="learning-resource">

                    <div className="resource-icon">
                      📖
                    </div>

                    <div className="resource-content">

                      <span>
                        Development Focus
                      </span>

                      <strong>
                        Improve {item.topic}
                      </strong>

                      <small>
                        Target level:{" "}
                        {item.required_level}/5
                      </small>

                    </div>

                  </div>

                )}

                <div className="learning-next">

  <strong>
    Next Action
  </strong>

  {learningStatus === "Completed" ? (

    <>

      <span>
        Your learning activity is complete.
        Re-assess this competency to measure
        your improvement.
      </span>
      <button
  className="reassess-button"
  onClick={() => {
    setReassessmentTopic(item.competency);
    setPage("studio");
  }}
>
  Re-assess {item.topic} →
</button>
      
    </>

  ) : (

    <span>
      Complete the recommended learning
      resource and then take another
      assessment to measure improvement.
    </span>

  )}

</div>
              </div>

            </div>

          );

        })}

    </div>

  </section>

)}
{/* COMPETENCY IMPROVEMENT HISTORY */}

{improvementHistory.length > 0 && (
  <section className="card">

    <div className="section-heading">
      <div>
        <h2>
          Competency Improvement
        </h2>

        <p className="subtitle">
          Track how your competency levels
          change after learning and re-assessment.
        </p>
      </div>
    </div>

    <div className="improvement-list">

      {improvementHistory.map(
        (item, index) => (
          <div
            className="improvement-card"
            key={`${item.topic}-${item.date}-${index}`}
          >

            <div className="improvement-main">

              <div>
                <strong>
                  {item.topic}
                </strong>

                <span className="improvement-date">
                  Assessed {new Date(item.date).toLocaleString()}
                </span>
              </div>

              <div
                className={
                  item.improvement > 0
                    ? "improvement-positive"
                    : item.improvement < 0
                    ? "improvement-negative"
                    : "improvement-neutral"
                }
              >
                {item.improvement > 0
                  ? `+${item.improvement}`
                  : item.improvement}
              </div>

            </div>

            <div className="improvement-levels">

              <div>
                <span>
                  Previous Level
                </span>

                <strong>
                  {item.initial_level}/5
                </strong>
              </div>

              <div className="improvement-arrow">
                →
              </div>

              <div>
                <span>
                  Current Level
                </span>

                <strong>
                  {item.final_level}/5
                </strong>
              </div>

              <div>
                <span>
                  Assessment Score
                </span>

                <strong>
                  {item.score}%
                </strong>
              </div>

            </div>

          </div>
        )
      )}

    </div>

  </section>
)}

          {/* RECOMMENDATIONS */}

          {recommendations.length >
            0 && (
              <section className="card">

                <div className="section-heading">
                  <div>
                    <h2>
                      Recommended Learning
                    </h2>

                    <p className="subtitle">
                      Learning resources aligned
                      with your competency gaps.
                    </p>
                  </div>
                </div>

                <div className="recommendation-list">

                  {recommendations.map(
                    (course, index) => (
                      <div
                        className="course-card"
                        key={
                          course.course_id ||
                          `${course.title}-${index}`
                        }
                      >

                        <div className="course-number">
                          {index + 1}
                        </div>

                        <div className="course-content">

                          <div className="course-top">

                            <div>
                              <h3>
                                {
                                  course.title
                                }
                              </h3>

                              <span className="provider">
                                {
                                  course.provider ||
                                  "Recommended Learning"
                                }
                              </span>
                            </div>

                            <div className="match">

                              <strong>
                                {course.match ??
                                  course.match_score ??
                                  "—"}
                              </strong>

                              <span>
                                Match
                              </span>

                            </div>

                          </div>

                          <div className="course-info">

                            {course.level && (
                              <span>
                                Level:{" "}
                                {
                                  course.level
                                }
                              </span>
                            )}

                            {course.duration && (
                              <span>
                                Duration:{" "}
                                {
                                  course.duration
                                }
                              </span>
                            )}

                            {course.format && (
                              <span>
                                Format:{" "}
                                {
                                  course.format
                                }
                              </span>
                            )}

                          </div>

                          {course.reasons &&
                            course.reasons.length >
                              0 && (
                              <div className="why">

                                <strong>
                                  Why this is
                                  recommended
                                </strong>

                                {course.reasons.map(
                                  (
                                    reason,
                                    reasonIndex
                                  ) => (
                                    <p
                                      key={`${course.course_id || course.title}-reason-${reasonIndex}`}
                                    >
                                      •{" "}
                                      {reason}
                                    </p>
                                  )
                                )}

                              </div>
                            )}

                        </div>

                      </div>
                    )
                  )}

                </div>

              </section>
            )}

          {/* -------------------------------- */}
          {/* VISUAL COMPETENCY PROGRESS */}
          {/* -------------------------------- */}

          {history.length > 0 && (
            <section className="card">

              <div className="section-heading">

                <div>
                  <h2>
                    📈 Competency Progress
                  </h2>

                  <p className="subtitle">
                    Visualize how your competency
                    level has changed across
                    assessments.
                  </p>
                </div>

                <div className="history-selector">

                  <label>
                    Topic
                  </label>

                  <select
                    value={historyTopic}
                    onChange={(event) =>
                      setHistoryTopic(
                        event.target.value
                      )
                    }
                  >
                    {historyTopics.map(
                      (topic) => (
                        <option
                          key={topic}
                          value={topic}
                        >
                          {topic}
                        </option>
                      )
                    )}
                  </select>

                </div>

              </div>

              {/* CHART */}

              {selectedHistory.length >
              0 ? (
                <div className="progress-chart">

                  {/* Y AXIS */}

                  <div className="chart-y-axis">

                    <span>5</span>
                    <span>4</span>
                    <span>3</span>
                    <span>2</span>
                    <span>1</span>
                    <span>0</span>

                  </div>

                  {/* CHART BODY */}

                  <div className="chart-body">

                    <div className="chart-grid-line line-5" />
                    <div className="chart-grid-line line-4" />
                    <div className="chart-grid-line line-3" />
                    <div className="chart-grid-line line-2" />
                    <div className="chart-grid-line line-1" />
                    <div className="chart-grid-line line-0" />

                    <div className="chart-columns">

                      {selectedHistory.map(
  (item, index) => {

    const level =
      Number(item.new_level) || 0;

  

    const percentage =
      Math.min(
        100,
        Math.max(
          0,
          (level / 5) * 100
        )
      );

    return (
      <div
        className="chart-column"
        key={`${item.topic}-${item.assessed_at}-${index}`}
      >

        <div className="chart-bar-wrapper">

          <div
            className="chart-bar"
            style={{
              height: `${percentage}%`
            }}
          />

        </div>
        <div className="chart-level">
          {level}/5
        </div>

        <div className="chart-score">
          {item.assessment_score ?? "N/A"}%
        </div>

        <div className="chart-label">
          Assessment {index + 1}
        </div>
        

      </div>
    );
  }
)}

                    </div>

                  </div>

                </div>
              ) : (
                <div className="empty-history">
                  No assessment history is
                  available for this topic yet.
                </div>
              )}

              {/* CHART LEGEND */}

              <div className="chart-legend">

                <div>
                  <span className="legend-bar" />
                  <span>
                    Competency level
                  </span>
                </div>

                <div>
                  <strong>
                    Score
                  </strong>
                  <span>
                    Assessment percentage
                  </span>
                </div>

              </div>

              {/* HISTORY TABLE */}

              <div className="history-table-wrapper">

                <table className="history-table">

                  <thead>
                    <tr>
                      <th>
                        Topic
                      </th>

                      <th>
                        Previous
                      </th>

                      <th>
  New Level
</th>

<th>
  Change
</th>

<th>
  Score
</th>

                      <th>
                        Assessment Date
                      </th>
                    </tr>
                  </thead>

                  <tbody>

                    {selectedHistory.map(
                      (item, index) => (
                        <tr
                          key={
                            item.id ||
                            `history-${index}`
                          }
                        >

                          <td>
                            <strong>
                              {item.topic}
                            </strong>
                          </td>

                          <td>
                            {item.previous_level ??
                              "N/A"}
                            /5
                          </td>

<td>
  <span className="table-level">
    {item.new_level}/5
  </span>
</td>

<td>
  {(() => {
    const change =
      Number(item.new_level) -
      Number(item.previous_level);

    return (
      <span
        className={
          change > 0
            ? "history-improvement positive"
            : change < 0
            ? "history-improvement negative"
            : "history-improvement neutral"
        }
      >
        {change > 0 ? "+" : ""}
        {change}
      </span>
    );
  })()}
</td>

<td>
  {item.assessment_score ??
    "N/A"}
  %
</td>

                          <td>
                            {new Date(
                              item.assessed_at
                            ).toLocaleString()}
                          </td>

                        </tr>
                      )
                    )}

                  </tbody>

                </table>

              </div>

            </section>
          )}

        </main>

        {/* FOOTER */}

        <footer className="footer">
          <strong>
            STATWISE AI
          </strong>

          <span>
            Competency Intelligence Platform
          </span>
        </footer>

      </div>
    );
  }

  // --------------------------------
  // Assessment Studio
  // --------------------------------

  return (
    <div className="app-shell">

      <header className="topbar">

        <div className="brand">

          <div className="brand-mark">
            SW
          </div>

          <div>
            <h1>
              STATWISE AI
            </h1>

            <span>
              Competency Intelligence Platform
            </span>
          </div>

        </div>

        <nav>

          <button
            className="nav-button"
            onClick={() =>
              setPage("dashboard")
            }
          >
            Dashboard
          </button>

          <button
            className="nav-button active"
            onClick={() =>
              setPage("assessment")
            }
          >
            Assessment Studio
          </button>

        </nav>

      </header>

      <main className="main-container">

        <AssessmentStudio
  initialTopic={reassessmentTopic}
/>

      </main>

    </div>
  );
}

export default App;