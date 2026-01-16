"""Evaluation runner for Multi-Agent Insurance Assistant testing.

Usage:
    # Run all tests
    python -m evaluation.runner

    # Run specific category
    python -m evaluation.runner --category individual_agent
    python -m evaluation.runner --category memory
    python -m evaluation.runner --category multi_agent
    python -m evaluation.runner --category edge_cases

    # Run specific subcategory
    python -m evaluation.runner --subcategory email_communications
    python -m evaluation.runner --subcategory chitchat

    # Run single test
    python -m evaluation.runner --id email_001

    # Run with verbose output
    python -m evaluation.runner --verbose

    # Run memory tests (sequential pairs)
    python -m evaluation.runner --memory-tests

    # Run with LLM answer validation
    python -m evaluation.runner --validate-answers
"""

import sys
import os
import json
import time
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.executor import execute_with_retry
from graph.orchestrator import MultiAgentOrchestrator
from agents.skill_router import SkillDetector
try:
    from .comprehensive_evaluation import (
        ALL_EVALUATION_QUESTIONS,
        get_questions_by_category,
        get_questions_by_subcategory,
        get_question_by_id,
        get_memory_test_sequences,
        get_evaluation_summary,
        COMPANY_INFO
    )
except ImportError:
    from comprehensive_evaluation import (
        ALL_EVALUATION_QUESTIONS,
        get_questions_by_category,
        get_questions_by_subcategory,
        get_question_by_id,
        get_memory_test_sequences,
        get_evaluation_summary,
        COMPANY_INFO
    )

# LLM Judge imports
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# =============================================================================
# LLM-AS-A-JUDGE EVALUATION
# =============================================================================

LLM_JUDGE_PROMPT = """You are an evaluation judge for an insurance assistant AI. Your job is to determine if the assistant's response correctly answers the question based on the expected answer criteria.

## Question
{question}

## Expected Answer
Type: {answer_type}
Expected Value: {expected_value}
Acceptable Variations: {acceptable_variations}

## Assistant's Response
{actual_response}

## Evaluation Criteria by Type:
- **exact**: Response must contain the exact value or one of the acceptable variations
- **contains**: Response must contain ALL the specified keywords/values
- **numeric_range**: Response must contain a number that matches or is very close to the expected value
- **list**: Response should contain multiple items as expected (check if it's a reasonable list)
- **open_ended**: Response should reasonably address the question (be lenient, focus on relevance)
- **clarification**: Response should ask for clarification or more details (look for questions, "could you specify", etc.)

## Your Task
Evaluate if the response is CORRECT based on the criteria above.

Respond in this exact JSON format:
{{
    "is_correct": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of why the answer is correct or incorrect",
    "matched_values": ["list of expected values found in response"],
    "missing_values": ["list of expected values NOT found in response"]
}}
"""


def get_llm_judge():
    """Get LLM instance for judging answers."""
    if not LLM_AVAILABLE:
        return None

    try:
        from config.settings import OPENAI_API_KEY, LLM_MODEL
        return ChatOpenAI(
            model=LLM_MODEL,
            temperature=0.0,  # Deterministic for evaluation
            api_key=OPENAI_API_KEY
        )
    except Exception as e:
        print(f"Warning: Could not initialize LLM judge: {e}")
        return None


def evaluate_answer_with_llm(
    question: str,
    expected_answer: Dict[str, Any],
    actual_response: str,
    llm: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Use LLM to evaluate if the response matches the expected answer.

    Args:
        question: The original question
        expected_answer: Dict with type, value, acceptable_variations
        actual_response: The assistant's actual response
        llm: Optional pre-initialized LLM instance

    Returns:
        Dict with is_correct, confidence, reasoning, etc.
    """
    if not actual_response:
        return {
            "is_correct": False,
            "confidence": 1.0,
            "reasoning": "No response provided",
            "matched_values": [],
            "missing_values": [expected_answer.get("value", "")]
        }

    answer_type = expected_answer.get("type", "open_ended")
    expected_value = expected_answer.get("value", "")
    acceptable_variations = expected_answer.get("acceptable_variations", [])

    # For open_ended type with no specific value, just check if there's a response
    if answer_type == "open_ended" and not expected_value:
        return {
            "is_correct": bool(actual_response and len(actual_response) > 10),
            "confidence": 0.8,
            "reasoning": "Open-ended question - response provided",
            "matched_values": [],
            "missing_values": []
        }

    # Try rule-based evaluation first for simple cases
    rule_result = evaluate_answer_with_rules(
        answer_type, expected_value, acceptable_variations, actual_response
    )
    if rule_result["confidence"] >= 0.9:
        return rule_result

    # Fall back to LLM for complex cases
    if llm is None:
        llm = get_llm_judge()

    if llm is None:
        # No LLM available, return rule-based result
        return rule_result

    try:
        prompt = ChatPromptTemplate.from_template(LLM_JUDGE_PROMPT)
        chain = prompt | llm

        result = chain.invoke({
            "question": question,
            "answer_type": answer_type,
            "expected_value": str(expected_value),
            "acceptable_variations": str(acceptable_variations),
            "actual_response": actual_response[:3000]  # Limit response length for LLM judge
        })

        # Parse LLM response
        response_text = result.content

        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            eval_result = json.loads(json_match.group())
            return eval_result
        else:
            # Fallback if JSON parsing fails
            return rule_result

    except Exception as e:
        print(f"Warning: LLM evaluation failed: {e}")
        return rule_result


def evaluate_answer_with_rules(
    answer_type: str,
    expected_value: Any,
    acceptable_variations: List[str],
    actual_response: str
) -> Dict[str, Any]:
    """
    Rule-based answer evaluation (faster, used as fallback).
    """
    response_lower = actual_response.lower()
    matched = []
    missing = []

    if answer_type == "exact":
        # Check exact value or variations
        values_to_check = [str(expected_value).lower()] + [str(v).lower() for v in acceptable_variations]
        for val in values_to_check:
            if val in response_lower:
                matched.append(val)
        is_correct = len(matched) > 0
        confidence = 0.95 if is_correct else 0.9

    elif answer_type == "contains":
        # Check all required values are present
        if isinstance(expected_value, list):
            values_to_check = [str(v).lower() for v in expected_value]
        else:
            values_to_check = [str(expected_value).lower()]

        for val in values_to_check:
            if val in response_lower:
                matched.append(val)
            else:
                missing.append(val)

        is_correct = len(missing) == 0
        confidence = 0.9 if is_correct else 0.85

    elif answer_type == "numeric_range":
        # Extract numbers from response and check
        numbers = re.findall(r'[\d,]+\.?\d*', actual_response.replace(',', ''))
        expected_num = float(str(expected_value).replace(',', '').replace('$', ''))

        is_correct = False
        for num_str in numbers:
            try:
                num = float(num_str)
                # Allow 10% tolerance
                if abs(num - expected_num) / max(expected_num, 1) < 0.1:
                    is_correct = True
                    matched.append(str(num))
                    break
            except ValueError:
                continue

        if not is_correct:
            missing.append(str(expected_value))
        confidence = 0.85

    elif answer_type == "list":
        # Check if response contains multiple items (heuristic)
        has_bullets = bool(re.search(r'[-•*]\s+\w+', actual_response))
        has_numbers = bool(re.search(r'\d+[.)]\s+\w+', actual_response))
        has_commas = actual_response.count(',') >= 2

        is_correct = has_bullets or has_numbers or has_commas or len(actual_response) > 100
        confidence = 0.7  # Lower confidence, LLM should verify

    elif answer_type == "clarification":
        # Check if response asks for clarification
        clarification_indicators = [
            '?', 'could you', 'can you', 'please specify', 'what do you mean',
            'clarify', 'more specific', 'which', 'what kind'
        ]
        matches = sum(1 for ind in clarification_indicators if ind in response_lower)
        is_correct = matches >= 1
        confidence = 0.8

    else:  # open_ended
        is_correct = bool(actual_response and len(actual_response) > 20)
        confidence = 0.6  # Low confidence, LLM should verify

    return {
        "is_correct": is_correct,
        "confidence": confidence,
        "reasoning": f"Rule-based evaluation for type '{answer_type}'",
        "matched_values": matched,
        "missing_values": missing
    }


def run_single_test(
    test_case: dict,
    verbose: bool = False,
    validate_answer: bool = False,
    llm_judge: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Run a single test case and return results.

    Args:
        test_case: Test case dictionary with question, expected_skill, etc.
        verbose: Whether to print detailed output
        validate_answer: Whether to validate the answer using LLM judge
        llm_judge: Pre-initialized LLM instance for answer validation

    Returns:
        Dictionary with test results
    """
    test_id = test_case["id"]
    question = test_case["question"]
    expected_skill = test_case["expected_skill"]
    company_id = test_case["company_id"]
    expected_answer = test_case.get("expected_answer", {})

    if verbose:
        print(f"\n{'='*60}")
        print(f"TEST: {test_id}")
        print(f"{'='*60}")
        print(f"Question: {question}")
        print(f"Expected Skill: {expected_skill}")
        print(f"Company ID: {company_id}")
        if validate_answer and expected_answer:
            print(f"Expected Answer Type: {expected_answer.get('type', 'N/A')}")
            print(f"Expected Value: {expected_answer.get('value', 'N/A')}")

    # Track timing
    start_time = time.time()

    # First, check skill detection (without executing)
    detected_skill = SkillDetector.detect_skill(question)
    skill_match = detected_skill == expected_skill

    if verbose:
        print(f"\nSkill Detection:")
        print(f"  Detected: {detected_skill}")
        print(f"  Expected: {expected_skill}")
        print(f"  Match: {'PASS' if skill_match else 'FAIL'}")

    # Execute the query using MultiAgentOrchestrator
    try:
        orchestrator = MultiAgentOrchestrator(company_id)
        result = orchestrator.process_query(
            user_question=question,
            session_id=f"eval_{test_id}",
            conversation_history=None
        )
        execution_success = result.get("success", False)
        execution_error = result.get("error")
        sql_generated = result.get("sql", "") or ""
        results_list = result.get("results") or []
        rows_returned = len(results_list)
        natural_response = result.get("natural_response", "") or ""
        actual_skill = result.get("skill", "unknown") or "unknown"

        # Agent tracking - NEW
        route_decision = result.get("route_decision", "unknown") or "unknown"
        trajectory = result.get("trajectory") or {}
        execution_path = trajectory.get("execution_path") or []
        documents_list = result.get("documents") or []
        documents_retrieved = len(documents_list)

    except Exception as e:
        execution_success = False
        execution_error = str(e)
        sql_generated = ""
        rows_returned = 0
        natural_response = ""
        actual_skill = "error"
        route_decision = "error"
        execution_path = []
        documents_retrieved = 0

    # Answer validation using LLM judge
    answer_validation = None
    answer_correct = None

    if validate_answer and expected_answer and execution_success:
        # LLM-as-a-judge evaluation
        answer_validation = evaluate_answer_with_llm(
            question=question,
            expected_answer=expected_answer,
            actual_response=natural_response,
            llm=llm_judge
        )
        answer_correct = answer_validation.get("is_correct", False)

        if verbose:
            print(f"\nAnswer Validation (LLM Judge):")
            print(f"  Correct: {'PASS' if answer_correct else 'FAIL'}")
            print(f"  Confidence: {answer_validation.get('confidence', 0):.2f}")
            print(f"  Reasoning: {answer_validation.get('reasoning', 'N/A')[:100]}")
            if answer_validation.get("matched_values"):
                print(f"  Matched: {answer_validation['matched_values']}")
            if answer_validation.get("missing_values"):
                print(f"  Missing: {answer_validation['missing_values']}")

    end_time = time.time()
    duration = end_time - start_time

    if verbose:
        print(f"\nExecution:")
        print(f"  Success: {execution_success}")
        print(f"  Actual Skill: {actual_skill}")
        print(f"  Route Decision: {route_decision}")
        print(f"  Execution Path: {' -> '.join(execution_path) if execution_path else 'N/A'}")
        print(f"  Rows Returned: {rows_returned}")
        print(f"  Documents Retrieved: {documents_retrieved}")
        print(f"  Duration: {duration:.2f}s")
        if execution_error:
            print(f"  Error: {execution_error}")
        if sql_generated:
            print(f"\nGenerated SQL:")
            print(f"  {sql_generated[:200]}...")
        if natural_response:
            print(f"\nNatural Response:")
            print(f"  {natural_response[:200]}...")

    # Determine overall test status
    # If validating answers, require answer to be correct too
    if validate_answer:
        test_passed = skill_match and execution_success and (answer_correct is True)
    else:
        test_passed = skill_match and execution_success

    # Check if expected agents match actual execution path
    expected_agents = test_case.get("expected_agents", [])
    expected_route = test_case.get("expected_route", "")
    agents_match = set(expected_agents) == set(execution_path) if expected_agents else None
    route_match = route_decision == expected_route if expected_route else None

    return {
        "test_id": test_id,
        "question": question,
        "category": test_case["category"],
        "subcategory": test_case.get("subcategory", ""),
        "description": test_case["description"],
        "passed": test_passed,
        "skill_detection": {
            "expected": expected_skill,
            "detected": detected_skill,
            "match": skill_match
        },
        "execution": {
            "success": execution_success,
            "error": execution_error,
            "sql": sql_generated,
            "rows_returned": rows_returned,
            "actual_skill": actual_skill
        },
        "agent_tracking": {
            "route_decision": route_decision,
            "expected_route": expected_route,
            "route_match": route_match,
            "execution_path": execution_path,
            "expected_agents": expected_agents,
            "agents_match": agents_match,
            "documents_retrieved": documents_retrieved
        },
        "answer_validation": answer_validation,
        "duration_seconds": duration,
        "natural_response": natural_response[:2000] if natural_response else ""
    }


def run_evaluation(
    questions: Optional[List[dict]] = None,
    category: Optional[str] = None,
    company_id: Optional[int] = None,
    verbose: bool = False,
    save_results: bool = True,
    validate_answers: bool = False
) -> Dict[str, Any]:
    """
    Run evaluation on multiple test questions.

    Args:
        questions: List of test cases (defaults to all TEST_QUESTIONS)
        category: Filter by category (emails, calls, sms, company, general)
        company_id: Override company ID for all tests
        verbose: Whether to print detailed output
        save_results: Whether to save results to JSON file
        validate_answers: Whether to validate answers using LLM judge

    Returns:
        Dictionary with evaluation summary and results
    """
    # Get questions to run
    if questions is None:
        if category:
            questions = get_questions_by_category(category)
        else:
            questions = ALL_EVALUATION_QUESTIONS

    # Override company_id if provided
    if company_id is not None:
        questions = [
            {**q, "company_id": company_id} for q in questions
        ]

    if not questions:
        print("No test questions to run!")
        return {"error": "No questions"}

    # Initialize LLM judge if validating answers
    llm_judge = None
    if validate_answers:
        llm_judge = get_llm_judge()
        if llm_judge:
            print("LLM Judge: Enabled")
        else:
            print("LLM Judge: Not available (will use rule-based evaluation)")

    print(f"\n{'#'*60}")
    print(f"MULTI-AGENT EVALUATION")
    print(f"{'#'*60}")
    print(f"Running {len(questions)} test(s)")
    if category:
        print(f"Category: {category}")
    print(f"Answer Validation: {'Enabled (LLM Judge)' if validate_answers else 'Disabled'}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}\n")

    results = []
    passed_count = 0
    failed_count = 0
    total_duration = 0

    # Track additional metrics when validating
    answer_correct_count = 0

    # Track agent routing metrics
    route_match_count = 0
    route_total = 0
    agents_match_count = 0
    agents_total = 0
    route_distribution = {}

    for i, test_case in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] Running test: {test_case['id']}...")

        try:
            result = run_single_test(
                test_case,
                verbose=verbose,
                validate_answer=validate_answers,
                llm_judge=llm_judge
            )
        except Exception as e:
            print(f"         ERROR: {e}")
            result = {
                "test_id": test_case["id"],
                "question": test_case["question"],
                "category": test_case["category"],
                "subcategory": test_case.get("subcategory", ""),
                "description": test_case.get("description", ""),
                "passed": False,
                "skill_detection": {"expected": test_case.get("expected_skill", ""), "detected": "error", "match": False},
                "execution": {"success": False, "error": str(e), "sql": "", "rows_returned": 0, "actual_skill": "error"},
                "agent_tracking": {"route_decision": "error", "expected_route": "", "route_match": None, "execution_path": [], "expected_agents": [], "agents_match": None, "documents_retrieved": 0},
                "answer_validation": None,
                "duration_seconds": 0,
                "natural_response": ""
            }

        results.append(result)

        if result["passed"]:
            passed_count += 1
            status = "PASS"
        else:
            failed_count += 1
            status = "FAIL"

        # Track answer validation metrics
        if validate_answers and result:
            if result.get("answer_validation", {}).get("is_correct"):
                answer_correct_count += 1

        # Track agent routing metrics
        agent_tracking = result.get("agent_tracking", {})
        if agent_tracking:
            route = agent_tracking.get("route_decision", "unknown")
            route_distribution[route] = route_distribution.get(route, 0) + 1

            if agent_tracking.get("route_match") is not None:
                route_total += 1
                if agent_tracking["route_match"]:
                    route_match_count += 1

            if agent_tracking.get("agents_match") is not None:
                agents_total += 1
                if agent_tracking["agents_match"]:
                    agents_match_count += 1

        total_duration += result["duration_seconds"]
        print(f"         {status} ({result['duration_seconds']:.2f}s)")

    # Summary
    pass_rate = (passed_count / len(questions)) * 100 if questions else 0

    summary = {
        "total_tests": len(questions),
        "passed": passed_count,
        "failed": failed_count,
        "pass_rate": f"{pass_rate:.1f}%",
        "total_duration_seconds": total_duration,
        "average_duration_seconds": total_duration / len(questions) if questions else 0,
        "timestamp": datetime.now().isoformat()
    }

    # Add answer validation metrics if enabled
    if validate_answers:
        answer_accuracy = (answer_correct_count / len(questions)) * 100 if questions else 0

        summary["answer_validation"] = {
            "answers_correct": answer_correct_count,
            "answer_accuracy": f"{answer_accuracy:.1f}%"
        }

    # Add agent tracking metrics
    route_accuracy = (route_match_count / route_total * 100) if route_total > 0 else None
    agents_accuracy = (agents_match_count / agents_total * 100) if agents_total > 0 else None

    summary["agent_tracking"] = {
        "route_distribution": route_distribution,
        "route_accuracy": f"{route_accuracy:.1f}%" if route_accuracy is not None else "N/A",
        "route_matches": f"{route_match_count}/{route_total}" if route_total > 0 else "N/A",
        "agents_accuracy": f"{agents_accuracy:.1f}%" if agents_accuracy is not None else "N/A",
        "agents_matches": f"{agents_match_count}/{agents_total}" if agents_total > 0 else "N/A"
    }

    # Print summary
    print(f"\n{'='*60}")
    print("EVALUATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Pass Rate: {summary['pass_rate']}")
    print(f"Total Duration: {summary['total_duration_seconds']:.2f}s")
    print(f"Avg Duration: {summary['average_duration_seconds']:.2f}s")

    # Agent tracking metrics
    print(f"\n--- Agent Tracking Metrics ---")
    print(f"Route Distribution: {route_distribution}")
    if route_total > 0:
        print(f"Route Accuracy: {summary['agent_tracking']['route_accuracy']} ({route_match_count}/{route_total})")
    if agents_total > 0:
        print(f"Agent Path Accuracy: {summary['agent_tracking']['agents_accuracy']} ({agents_match_count}/{agents_total})")

    if validate_answers:
        print(f"\n--- Answer Validation Metrics ---")
        print(f"Answers Correct: {summary['answer_validation']['answers_correct']}/{len(questions)}")
        print(f"Answer Accuracy: {summary['answer_validation']['answer_accuracy']}")

    # Show failed tests
    if failed_count > 0:
        print(f"\n{'='*60}")
        print("FAILED TESTS:")
        print(f"{'='*60}")
        for r in results:
            if not r["passed"]:
                print(f"\n  {r['test_id']}: {r['question'][:50]}...")
                if not r["skill_detection"]["match"]:
                    print(f"    - Skill mismatch: expected '{r['skill_detection']['expected']}', got '{r['skill_detection']['detected']}'")
                if not r["execution"]["success"]:
                    print(f"    - Execution error: {r['execution']['error'][:100] if r['execution']['error'] else 'Unknown'}")

    # Save results
    if save_results:
        # Get company_id for filename
        test_company_id = questions[0]["company_id"] if questions else "unknown"
        output_file = f"company_{test_company_id}_test.json"
        output_path = os.path.join(os.path.dirname(__file__), output_file)

        # Format results with Q&A for easy reading
        qa_results = []
        for r in results:
            result_entry = {
                "test_id": r["test_id"],
                "category": r["category"],
                "subcategory": r.get("subcategory", ""),
                "question": r["question"],
                "answer": r["natural_response"],
                "passed": r["passed"],
                "skill_detected": r["skill_detection"]["detected"],
                "skill_expected": r["skill_detection"]["expected"],
                "skill_match": r["skill_detection"]["match"],
                "sql_generated": r["execution"]["sql"],
                "rows_returned": r["execution"]["rows_returned"],
                "duration_seconds": r["duration_seconds"],
                "error": r["execution"]["error"]
            }

            # Add agent tracking info
            if r.get("agent_tracking"):
                result_entry["agent_tracking"] = {
                    "route_decision": r["agent_tracking"]["route_decision"],
                    "expected_route": r["agent_tracking"]["expected_route"],
                    "route_match": r["agent_tracking"]["route_match"],
                    "execution_path": r["agent_tracking"]["execution_path"],
                    "expected_agents": r["agent_tracking"]["expected_agents"],
                    "agents_match": r["agent_tracking"]["agents_match"],
                    "documents_retrieved": r["agent_tracking"]["documents_retrieved"]
                }

            # Add answer validation if present
            if r.get("answer_validation"):
                result_entry["answer_validation"] = {
                    "is_correct": r["answer_validation"].get("is_correct"),
                    "confidence": r["answer_validation"].get("confidence"),
                    "reasoning": r["answer_validation"].get("reasoning"),
                    "matched_values": r["answer_validation"].get("matched_values", []),
                    "missing_values": r["answer_validation"].get("missing_values", [])
                }

            qa_results.append(result_entry)

        with open(output_path, "w") as f:
            json.dump({
                "company_id": test_company_id,
                "summary": summary,
                "questions_and_answers": qa_results
            }, f, indent=2, default=str)

        print(f"\nResults saved to: {output_path}")

    return {
        "summary": summary,
        "results": results
    }


def run_memory_evaluation(verbose: bool = False, save_results: bool = True) -> Dict[str, Any]:
    """
    Run memory-based evaluation with sequential question pairs.

    This tests conversation memory by running setup questions followed by
    follow-up questions that require context from the previous answer.
    """
    sequences = get_memory_test_sequences()

    print(f"\n{'#'*60}")
    print("MEMORY EVALUATION (Sequential Question Pairs)")
    print(f"{'#'*60}")
    print(f"Running {len(sequences)} memory test sequences")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}\n")

    results = []
    passed_count = 0
    failed_count = 0
    total_duration = 0

    for i, sequence in enumerate(sequences, 1):
        setup_q = sequence[0]
        followup_q = sequence[1]

        print(f"\n[Sequence {i}/{len(sequences)}]")
        print(f"  Setup: {setup_q['question']}")

        # Run setup question
        setup_result = run_single_test(setup_q, verbose=verbose)
        results.append(setup_result)
        total_duration += setup_result["duration_seconds"]

        if setup_result["passed"]:
            passed_count += 1
            print(f"  Setup Result: PASS")
        else:
            failed_count += 1
            print(f"  Setup Result: FAIL")

        # Run follow-up with memory context
        print(f"  Follow-up: {followup_q['question']}")

        # Create conversation history from setup
        conversation_history = [
            {"question": setup_q["question"], "answer": setup_result["natural_response"]}
        ]

        followup_result = run_single_test(followup_q, verbose=verbose)
        results.append(followup_result)
        total_duration += followup_result["duration_seconds"]

        if followup_result["passed"]:
            passed_count += 1
            print(f"  Follow-up Result: PASS")
        else:
            failed_count += 1
            print(f"  Follow-up Result: FAIL")

    # Summary
    total_tests = len(results)
    pass_rate = (passed_count / total_tests) * 100 if total_tests else 0

    summary = {
        "total_tests": total_tests,
        "total_sequences": len(sequences),
        "passed": passed_count,
        "failed": failed_count,
        "pass_rate": f"{pass_rate:.1f}%",
        "total_duration_seconds": total_duration,
        "average_duration_seconds": total_duration / total_tests if total_tests else 0,
        "timestamp": datetime.now().isoformat()
    }

    print(f"\n{'='*60}")
    print("MEMORY EVALUATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total Sequences: {summary['total_sequences']}")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Pass Rate: {summary['pass_rate']}")

    return {"summary": summary, "results": results}


def main():
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Multi-Agent Insurance Assistant Evaluation Runner")
    parser.add_argument("--category", "-c", type=str,
                        help="Run tests for specific category (individual_agent, memory, multi_agent, edge_cases)")
    parser.add_argument("--subcategory", "-s", type=str,
                        help="Run tests for specific subcategory (email_communications, phone_calls, chitchat, etc.)")
    parser.add_argument("--company-id", type=int, help="Override company ID for all tests")
    parser.add_argument("--id", type=str, help="Run a single test by ID")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-save", action="store_true", help="Don't save results to file")
    parser.add_argument("--memory-tests", action="store_true", help="Run memory tests as sequential pairs")
    parser.add_argument("--summary", action="store_true", help="Show evaluation summary statistics")
    parser.add_argument("--validate-answers", action="store_true",
                        help="Enable LLM-as-a-judge answer validation")

    args = parser.parse_args()

    # Show summary
    if args.summary:
        summary = get_evaluation_summary()
        print(f"\n{'='*60}")
        print("EVALUATION FRAMEWORK SUMMARY")
        print(f"{'='*60}")
        print(f"\nTest Company: {COMPANY_INFO['name']}")
        print(f"Company ID: {COMPANY_INFO['id']}")
        print(f"\nTotal Questions: {summary['total_questions']}")
        print("\nBy Category:")
        for cat, count in summary["by_category"].items():
            print(f"  {cat}: {count}")
        print("\nBy Subcategory:")
        for subcat, count in sorted(summary["by_subcategory"].items()):
            print(f"  {subcat}: {count}")
        print("\nBy Complexity:")
        for comp, count in summary["by_complexity"].items():
            print(f"  {comp}: {count}")
        print(f"\nMemory Questions: {summary['memory_questions']}")
        return

    # Run memory tests
    if args.memory_tests:
        run_memory_evaluation(verbose=args.verbose, save_results=not args.no_save)
        return

    # Run single test
    if args.id:
        test_case = get_question_by_id(args.id)
        if not test_case:
            print(f"Test ID '{args.id}' not found!")
            print(f"\nAvailable IDs by category:")
            for cat in ["individual_agent", "memory", "multi_agent", "edge_cases"]:
                ids = [q["id"] for q in get_questions_by_category(cat)]
                print(f"  {cat}: {ids[:5]}..." if len(ids) > 5 else f"  {cat}: {ids}")
            sys.exit(1)

        llm_judge = get_llm_judge() if args.validate_answers else None
        result = run_single_test(
            test_case,
            verbose=True,
            validate_answer=args.validate_answers,
            llm_judge=llm_judge
        )
        print(f"\n{'='*60}")
        print(f"RESULT: {'PASS' if result['passed'] else 'FAIL'}")
        print(f"{'='*60}")
        return

    # Run by subcategory
    if args.subcategory:
        questions = get_questions_by_subcategory(args.subcategory)
        if not questions:
            print(f"Subcategory '{args.subcategory}' not found!")
            summary = get_evaluation_summary()
            print(f"Available subcategories: {list(summary['by_subcategory'].keys())}")
            sys.exit(1)
        run_evaluation(
            questions=questions,
            company_id=args.company_id,
            verbose=args.verbose,
            save_results=not args.no_save,
            validate_answers=args.validate_answers
        )
        return

    # Run full evaluation or by category
    run_evaluation(
        category=args.category,
        company_id=args.company_id,
        verbose=args.verbose,
        save_results=not args.no_save,
        validate_answers=args.validate_answers
    )


if __name__ == "__main__":
    main()