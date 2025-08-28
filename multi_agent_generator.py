"""
Multi-Agent Code Generation System
Replaces single-agent code generation with coordinated team of specialized agents
"""

import asyncio
import os
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import anthropic

from spec_parser import ServiceSpec


class AgentRole(Enum):
    """Available agent roles"""
    CODE_GENERATOR = "code_generator"
    VALIDATOR = "validator" 
    TEST_GENERATOR = "test_generator"


@dataclass
class ValidationResult:
    """Result from validation agent"""
    score: float  # 0.0 - 1.0
    spec_compliance: float  # 0.0 - 1.0 
    issues: List[str]
    critical_issues: List[str]
    suggestions: List[str]
    passed: bool


@dataclass
class GenerationAttempt:
    """Single code generation attempt"""
    code_files: Dict[str, str]
    validation: Optional[ValidationResult]
    generation_time: float
    agent_version: str  # "primary" or "alternative"


class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self, client: anthropic.Anthropic, model: str, debug: bool = False):
        self.client = client
        self.model = model
        self.debug = debug
        self.role = None  # Set by subclasses
    
    def _log_debug(self, message: str):
        """Debug logging"""
        if self.debug:
            print(f"🤖 [{self.role.value.upper()}] {message}")
    
    async def _call_claude(self, prompt: str, max_tokens: int = 4000) -> str:
        """Make Claude API call with error handling and timeout"""
        try:
            self._log_debug(f"Making Claude API call (tokens: {max_tokens})")
            
            # Add timeout to the API call (2 minutes for large responses)
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.messages.create,
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                ),
                timeout=120.0  # 2 minute timeout
            )
            
            result = response.content[0].text
            self._log_debug(f"Received response ({len(result)} chars)")
            return result
            
        except asyncio.TimeoutError:
            self._log_debug("Claude API call timed out after 120 seconds")
            raise TimeoutError("Claude API call timeout")
        except Exception as e:
            self._log_debug(f"API call failed: {str(e)}")
            raise
    
    def _format_spec_for_prompt(self, spec: ServiceSpec) -> str:
        """Format ServiceSpec object into markdown text for prompts"""
        spec_text = f"# Service Name: {spec.name}\n"
        spec_text += f"Description: {spec.description}\n"
        spec_text += f"Runtime: {spec.runtime}\n\n"
        
        # Add endpoints section
        if spec.endpoints:
            spec_text += "## Endpoints\n\n"
            for endpoint in spec.endpoints:
                spec_text += f"### {endpoint.get('method', 'GET')} {endpoint.get('path', '/')}\n"
                if endpoint.get('description'):
                    spec_text += f"- Description: {endpoint['description']}\n"
                if endpoint.get('input'):
                    spec_text += f"- Input: {endpoint['input']}\n"
                if endpoint.get('output'):
                    spec_text += f"- Output: {endpoint['output']}\n"
                if endpoint.get('auth') and endpoint['auth'] != 'None':
                    spec_text += f"- Auth: {endpoint['auth']}\n"
                spec_text += "\n"
        
        # Add models section
        if spec.models:
            spec_text += "## Models\n\n"
            for model in spec.models:
                spec_text += f"### {model.get('name', 'Model')}\n"
                for field in model.get('fields', []):
                    spec_text += f"- {field}\n"
                spec_text += "\n"
        
        # Add optional sections
        if spec.business_logic:
            spec_text += "## Business Logic\n\n"
            spec_text += f"{spec.business_logic}\n\n"
        
        if spec.database:
            spec_text += "## Database\n\n"
            spec_text += f"{spec.database}\n\n"
            
        if spec.deployment:
            spec_text += "## Deployment\n\n"
            spec_text += f"{spec.deployment}\n\n"
        
        return spec_text.strip()


class CodeGeneratorAgent(BaseAgent):
    """Agent specialized in code generation"""
    
    def __init__(self, client: anthropic.Anthropic, model: str, debug: bool = False):
        super().__init__(client, model, debug)
        self.role = AgentRole.CODE_GENERATOR
    
    async def generate_primary(self, spec: ServiceSpec) -> Dict[str, str]:
        """Generate primary code version (optimized for readability and maintainability)"""
        self._log_debug("Generating primary code version")
        
        prompt = self._build_primary_prompt(spec)
        response = await self._call_claude(prompt, max_tokens=12000)
        
        return self._parse_code_response(response)
    
    async def generate_alternative(self, spec: ServiceSpec, style: str = "defensive") -> Dict[str, str]:
        """Generate alternative code version with different approach"""
        self._log_debug(f"Generating alternative code version (style: {style})")
        
        prompt = self._build_alternative_prompt(spec, style)
        response = await self._call_claude(prompt, max_tokens=12000)
        
        return self._parse_code_response(response)
    
    async def refine_code(self, spec: ServiceSpec, current_code: Dict[str, str], 
                         validation_issues: List[str]) -> Dict[str, str]:
        """Refine code based on validation feedback"""
        self._log_debug("Refining code based on validation feedback")
        
        prompt = self._build_refinement_prompt(spec, current_code, validation_issues)
        response = await self._call_claude(prompt, max_tokens=12000)
        
        return self._parse_code_response(response)
    
    def _build_primary_prompt(self, spec: ServiceSpec) -> str:
        """Build prompt for primary code generation"""
        spec_text = self._format_spec_for_prompt(spec)
        return f"""Generate production-ready {spec.runtime} code for this API specification.

SPECIFICATION:
{spec_text}

REQUIREMENTS:
- Focus on clean, readable, maintainable code
- Include comprehensive error handling
- Use modern best practices for {spec.runtime}
- Generate complete working application
- Include proper logging and validation
- Ensure all endpoints from spec are implemented

OUTPUT FORMAT:
Provide the code files in this exact format:

```json
{{
  "index.js": "// main application file content here",
  "package.json": "// package.json content here", 
  "Dockerfile": "// Dockerfile content here",
  "README.md": "// API documentation here"
}}
```

Generate complete, working, production-ready code that fully implements the specification."""

    def _build_alternative_prompt(self, spec: ServiceSpec, style: str) -> str:
        """Build prompt for alternative code generation"""
        style_instructions = {
            "defensive": "Focus on maximum error handling, input validation, and fault tolerance",
            "performance": "Focus on performance optimization, caching, and efficiency",
            "minimal": "Focus on minimal dependencies and lightweight implementation"
        }
        
        spec_content = self._format_spec_for_prompt(spec)
        return f"""Generate an alternative {spec.runtime} implementation for this API specification.

SPECIFICATION:
{spec_content}

ALTERNATIVE APPROACH:
{style_instructions.get(style, style)}

REQUIREMENTS:
- Take a different architectural approach than typical implementations
- {style_instructions.get(style, 'Use alternative patterns and techniques')}
- Generate complete working application
- Ensure all endpoints from spec are implemented
- Include comprehensive comments explaining the approach

OUTPUT FORMAT:
Provide the code files in this exact format:

```json
{{
  "index.js": "// main application file content here",
  "package.json": "// package.json content here", 
  "Dockerfile": "// Dockerfile content here",
  "README.md": "// API documentation here"
}}
```

Generate complete, working, production-ready code that fully implements the specification."""

    def _build_refinement_prompt(self, spec: ServiceSpec, current_code: Dict[str, str], 
                                issues: List[str]) -> str:
        """Build prompt for code refinement"""
        code_summary = "\n".join([f"**{filename}**:\n{content[:500]}..." 
                                 for filename, content in current_code.items()])
        
        spec_content = self._format_spec_for_prompt(spec)
        return f"""Refine this {spec.runtime} code to address the validation issues found.

ORIGINAL SPECIFICATION:
{spec_content}

CURRENT CODE:
{code_summary}

VALIDATION ISSUES TO FIX:
{chr(10).join(f'- {issue}' for issue in issues)}

REQUIREMENTS:
- Fix all listed validation issues
- Maintain the overall architecture and approach
- Ensure all endpoints from spec are still implemented
- Keep the code clean and production-ready
- Only modify what's necessary to fix the issues

OUTPUT FORMAT:
Provide the refined code files in this exact format:

```json
{{
  "index.js": "// refined main application file content here",
  "package.json": "// refined package.json content here", 
  "Dockerfile": "// refined Dockerfile content here",
  "README.md": "// refined API documentation here"
}}
```

Generate the complete refined code that addresses all validation issues."""

    def _parse_code_response(self, response: str) -> Dict[str, str]:
        """Parse Claude's response to extract code files"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("JSON parsing timeout")
        
        try:
            # Set a 30-second timeout for JSON parsing
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)
            
            # Look for JSON block in response
            start_marker = "```json"
            end_marker = "```"
            
            start_idx = response.find(start_marker)
            if start_idx == -1:
                raise ValueError("No JSON code block found in response")
            
            start_idx += len(start_marker)
            end_idx = response.find(end_marker, start_idx)
            
            if end_idx == -1:
                # Try to find the end of JSON even if closing ``` is missing
                json_content = response[start_idx:].strip()
                # Try to fix incomplete JSON by adding closing brace if needed
                if json_content and not json_content.endswith('}'):
                    json_content = json_content.rstrip(',') + '}'
            else:
                json_content = response[start_idx:end_idx].strip()
            
            # Try to parse the JSON
            code_files = json.loads(json_content)
            
            # Cancel the alarm
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
            
            # Validate that we got a dictionary with string keys and values
            if not isinstance(code_files, dict):
                raise ValueError("Response is not a JSON object")
                
            for key, value in code_files.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise ValueError(f"Invalid file entry: {key}")
            
            self._log_debug(f"Parsed {len(code_files)} code files")
            return code_files
            
        except (json.JSONDecodeError, TimeoutError) as e:
            # Cancel alarm
            try:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler if 'old_handler' in locals() else signal.SIG_DFL)
            except:
                pass
                
            self._log_debug(f"JSON parsing failed: {str(e)}")
            # Try to extract files using regex pattern matching as fallback
            return self._extract_files_with_regex(response)
        except Exception as e:
            # Cancel alarm
            try:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler if 'old_handler' in locals() else signal.SIG_DFL)
            except:
                pass
                
            self._log_debug(f"Failed to parse code response: {str(e)}")
            # Last resort fallback: return response as single file
            return {"generated_code.txt": response}
    
    def _extract_files_with_regex(self, response: str) -> Dict[str, str]:
        """Fallback method to extract files using regex patterns with timeout"""
        import re
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Regex processing timeout")
        
        files = {}
        
        try:
            # Set a 10-second timeout for regex processing
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(10)
            
            # Simple and fast extraction - just find the filenames and approximate content
            # This is much faster than complex regex with DOTALL
            
            # Look for common file patterns in the response
            filenames = ["index.js", "package.json", "Dockerfile", "README.md", "main.js", "app.js"]
            
            for filename in filenames:
                # Look for pattern: "filename": "content"
                pattern = f'"{filename}"\\s*:\\s*"'
                match = re.search(pattern, response)
                if match:
                    content_start = match.end()
                    
                    # Find the end by looking for the next quote that's not escaped
                    # But limit search to avoid hanging on very long content
                    search_limit = min(content_start + 20000, len(response))
                    content_section = response[content_start:search_limit]
                    
                    # Simple approach: find first occurrence of ", that looks like end of field
                    # This won't be perfect but will be fast and usually work
                    end_patterns = ['",\\s*"', '"}', '"\\s*}']
                    content_end = len(content_section)
                    
                    for end_pattern in end_patterns:
                        match_end = re.search(end_pattern, content_section)
                        if match_end:
                            content_end = match_end.start()
                            break
                    
                    if content_end > 0:
                        content = content_section[:content_end]
                        # Basic unescaping
                        content = content.replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
                        files[filename] = content
            
            # Cancel the alarm
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
            
        except TimeoutError:
            self._log_debug("Regex processing timed out, using simple fallback")
            # Cancel alarm and restore handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler if 'old_handler' in locals() else signal.SIG_DFL)
            
            # Simple fallback - return truncated response
            truncated_response = response[:5000] + "\n... (truncated due to timeout)" if len(response) > 5000 else response
            return {"generated_code.txt": truncated_response}
        
        except Exception as e:
            # Cancel alarm if it's still set
            try:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler if 'old_handler' in locals() else signal.SIG_DFL)
            except:
                pass
            
            self._log_debug(f"Regex extraction failed: {str(e)}")
            truncated_response = response[:5000] + "\n... (truncated due to error)" if len(response) > 5000 else response
            return {"generated_code.txt": truncated_response}
        
        if files:
            self._log_debug(f"Extracted {len(files)} files using fast regex")
            return files
        else:
            # No files extracted, return truncated response
            truncated_response = response[:5000] + "\n... (no files found)" if len(response) > 5000 else response
            return {"generated_code.txt": truncated_response}


class ValidatorAgent(BaseAgent):
    """Agent specialized in code validation"""
    
    def __init__(self, client: anthropic.Anthropic, model: str, debug: bool = False):
        super().__init__(client, model, debug)
        self.role = AgentRole.VALIDATOR
    
    async def validate(self, spec: ServiceSpec, code_files: Dict[str, str]) -> ValidationResult:
        """Validate code against specification"""
        self._log_debug("Validating code against specification")
        
        prompt = self._build_validation_prompt(spec, code_files)
        response = await self._call_claude(prompt, max_tokens=2000)
        
        return self._parse_validation_response(response)
    
    def _build_validation_prompt(self, spec: ServiceSpec, code_files: Dict[str, str]) -> str:
        """Build validation prompt"""
        code_summary = "\n".join([f"**{filename}**:\n{content}" 
                                 for filename, content in code_files.items()])
        
        spec_content = self._format_spec_for_prompt(spec)
        return f"""Validate this generated code against the original specification.

ORIGINAL SPECIFICATION:
{spec_content}

GENERATED CODE:
{code_summary}

VALIDATION CRITERIA:
1. Spec Compliance: All endpoints implemented with correct HTTP methods
2. Data Models: All specified models/fields present
3. Error Handling: Proper error responses and validation
4. Code Quality: Clean, maintainable, follows best practices
5. Completeness: No missing functionality from spec
6. Runtime Compatibility: Correct for specified runtime ({spec.runtime})

OUTPUT FORMAT:
Provide validation results in this exact JSON format:

```json
{{
  "overall_score": 0.85,
  "spec_compliance": 0.90,
  "issues": [
    "Missing validation for email format in POST /users",
    "GET /users/{id} doesn't handle non-existent IDs"
  ],
  "critical_issues": [
    "POST /users endpoint missing entirely"
  ],
  "suggestions": [
    "Add input validation middleware",
    "Implement proper error response format"
  ],
  "detailed_analysis": "Detailed explanation of findings..."
}}
```

Be thorough and specific in your validation. A score of 0.8+ indicates production-ready code."""

    def _parse_validation_response(self, response: str) -> ValidationResult:
        """Parse validation response"""
        try:
            # Look for JSON block in response
            start_marker = "```json"
            end_marker = "```"
            
            start_idx = response.find(start_marker)
            if start_idx == -1:
                raise ValueError("No JSON validation block found")
            
            start_idx += len(start_marker)
            end_idx = response.find(end_marker, start_idx)
            
            if end_idx == -1:
                raise ValueError("Malformed JSON validation block")
            
            json_content = response[start_idx:end_idx].strip()
            validation_data = json.loads(json_content)
            
            result = ValidationResult(
                score=validation_data.get("overall_score", 0.0),
                spec_compliance=validation_data.get("spec_compliance", 0.0),
                issues=validation_data.get("issues", []),
                critical_issues=validation_data.get("critical_issues", []),
                suggestions=validation_data.get("suggestions", []),
                passed=validation_data.get("overall_score", 0.0) >= 0.8
            )
            
            self._log_debug(f"Validation score: {result.score:.2f}, Passed: {result.passed}")
            return result
            
        except Exception as e:
            self._log_debug(f"Failed to parse validation response: {str(e)}")
            # Fallback validation result
            return ValidationResult(
                score=0.5,
                spec_compliance=0.5,
                issues=["Failed to parse validation response"],
                critical_issues=["Validation parsing error"],
                suggestions=["Review validation logic"],
                passed=False
            )


class TestGeneratorAgent(BaseAgent):
    """Agent specialized in test generation"""
    
    def __init__(self, client: anthropic.Anthropic, model: str, debug: bool = False):
        super().__init__(client, model, debug)
        self.role = AgentRole.TEST_GENERATOR
    
    async def generate_tests(self, spec: ServiceSpec, code_files: Dict[str, str]) -> Dict[str, str]:
        """Generate comprehensive tests for the service"""
        self._log_debug("Generating comprehensive tests")
        
        prompt = self._build_test_prompt(spec, code_files)
        response = await self._call_claude(prompt, max_tokens=3000)
        
        return self._parse_test_response(response)
    
    def _build_test_prompt(self, spec: ServiceSpec, code_files: Dict[str, str]) -> str:
        """Build test generation prompt"""
        main_file = code_files.get("index.js", code_files.get("main.py", ""))
        
        spec_content = self._format_spec_for_prompt(spec)
        return f"""Generate comprehensive tests for this API service.

SPECIFICATION:
{spec_content}

MAIN APPLICATION CODE:
{main_file[:1500]}...

TEST REQUIREMENTS:
- Unit tests for core functions
- Integration tests for API endpoints  
- Validation tests for input/output
- Error handling tests
- Edge case testing
- Performance/load testing setup

OUTPUT FORMAT:
Provide test files in this exact format:

```json
{{
  "test/unit.test.js": "// unit test content here",
  "test/integration.test.js": "// integration test content here",
  "test/api.test.js": "// API endpoint tests here",
  "jest.config.js": "// Jest configuration here"
}}
```

Generate complete, runnable tests that thoroughly validate the service."""

    def _parse_test_response(self, response: str) -> Dict[str, str]:
        """Parse test generation response"""
        try:
            # Look for JSON block in response
            start_marker = "```json"
            end_marker = "```"
            
            start_idx = response.find(start_marker)
            if start_idx == -1:
                raise ValueError("No JSON test block found")
            
            start_idx += len(start_marker)
            end_idx = response.find(end_marker, start_idx)
            
            if end_idx == -1:
                raise ValueError("Malformed JSON test block")
            
            json_content = response[start_idx:end_idx].strip()
            test_files = json.loads(json_content)
            
            self._log_debug(f"Generated {len(test_files)} test files")
            return test_files
            
        except Exception as e:
            self._log_debug(f"Failed to parse test response: {str(e)}")
            return {"test_generation_error.txt": f"Failed to generate tests: {str(e)}"}


class MultiAgentOrchestrator:
    """Orchestrates the multi-agent code generation system"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, 
                 debug: bool = False, quality_threshold: float = 0.8):
        self.client = anthropic.Anthropic(api_key=api_key or os.getenv('ANTHROPIC_API_KEY'))
        self.model = model or os.getenv('CLAUDE_MODEL') or "claude-sonnet-4-20250514"
        self.debug = debug
        self.quality_threshold = quality_threshold
        self.max_iterations = 3
        
        # Initialize agents
        self.code_generator = CodeGeneratorAgent(self.client, self.model, debug)
        self.validator = ValidatorAgent(self.client, self.model, debug)
        self.test_generator = TestGeneratorAgent(self.client, self.model, debug)
        
        self._log_debug(f"Initialized multi-agent system (model: {self.model})")
    
    def _log_debug(self, message: str):
        """Debug logging"""
        if self.debug:
            print(f"🎯 [ORCHESTRATOR] {message}")
    
    async def generate_with_validation(self, spec: ServiceSpec) -> Tuple[Dict[str, str], ValidationResult]:
        """Main entry point: generate code with multi-agent validation"""
        self._log_debug("Starting multi-agent code generation")
        start_time = time.time()
        
        try:
            # Phase 1: Generate multiple code versions
            self._log_debug("Phase 1: Generating code versions")
            code_versions = await self._generate_code_versions(spec)
            
            # Phase 2: Validate all versions
            self._log_debug("Phase 2: Validating code versions")
            validated_attempts = await self._validate_code_versions(spec, code_versions)
            
            # Phase 3: Select best version or iterate
            self._log_debug("Phase 3: Selecting best version")
            best_attempt = self._select_best_attempt(validated_attempts)
            
            # Phase 4: Refinement loop if needed
            if not best_attempt.validation.passed:
                self._log_debug("Phase 4: Starting refinement loop")
                best_attempt = await self._refinement_loop(spec, best_attempt)
            
            generation_time = time.time() - start_time
            self._log_debug(f"Multi-agent generation completed in {generation_time:.2f}s")
            
            return best_attempt.code_files, best_attempt.validation
            
        except Exception as e:
            self._log_debug(f"Multi-agent generation failed: {str(e)}")
            # Fallback to single-agent generation
            return await self._fallback_generation(spec)
    
    async def _generate_code_versions(self, spec: ServiceSpec) -> List[GenerationAttempt]:
        """Generate multiple code versions in parallel"""
        start_time = time.time()
        
        # Generate primary and alternative versions
        primary_task = self.code_generator.generate_primary(spec)
        alternative_task = self.code_generator.generate_alternative(spec, "defensive")
        
        results = await asyncio.gather(primary_task, alternative_task, return_exceptions=True)
        
        attempts = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self._log_debug(f"Code generation {i} failed: {str(result)}")
                continue
            
            attempt = GenerationAttempt(
                code_files=result,
                validation=None,
                generation_time=time.time() - start_time,
                agent_version="primary" if i == 0 else "alternative"
            )
            attempts.append(attempt)
        
        self._log_debug(f"Generated {len(attempts)} code versions")
        return attempts
    
    async def _validate_code_versions(self, spec: ServiceSpec, 
                                    attempts: List[GenerationAttempt]) -> List[GenerationAttempt]:
        """Validate all code versions in parallel"""
        if not attempts:
            return []
        
        validation_tasks = [
            self.validator.validate(spec, attempt.code_files) 
            for attempt in attempts
        ]
        
        validations = await asyncio.gather(*validation_tasks, return_exceptions=True)
        
        for i, (attempt, validation) in enumerate(zip(attempts, validations)):
            if isinstance(validation, Exception):
                self._log_debug(f"Validation {i} failed: {str(validation)}")
                # Create default validation result
                validation = ValidationResult(
                    score=0.0, spec_compliance=0.0, issues=["Validation failed"],
                    critical_issues=["Validation error"], suggestions=[], passed=False
                )
            
            attempt.validation = validation
            self._log_debug(f"Attempt {i} score: {validation.score:.2f}")
        
        return attempts
    
    def _select_best_attempt(self, attempts: List[GenerationAttempt]) -> GenerationAttempt:
        """Select the best code version based on validation scores"""
        if not attempts:
            raise Exception("No valid code attempts to select from")
        
        # Sort by validation score (highest first)
        attempts.sort(key=lambda a: a.validation.score if a.validation else 0, reverse=True)
        
        best = attempts[0]
        self._log_debug(f"Selected {best.agent_version} version (score: {best.validation.score:.2f})")
        
        return best
    
    async def _refinement_loop(self, spec: ServiceSpec, 
                             attempt: GenerationAttempt) -> GenerationAttempt:
        """Iteratively refine code until quality threshold is met"""
        current_attempt = attempt
        
        for iteration in range(self.max_iterations):
            if current_attempt.validation.score >= self.quality_threshold:
                break
            
            self._log_debug(f"Refinement iteration {iteration + 1}/{self.max_iterations}")
            
            # Get specific issues to fix
            issues_to_fix = (
                current_attempt.validation.critical_issues + 
                current_attempt.validation.issues[:3]  # Limit to top 3 issues
            )
            
            if not issues_to_fix:
                break
            
            # Refine the code
            try:
                refined_code = await self.code_generator.refine_code(
                    spec, current_attempt.code_files, issues_to_fix
                )
                
                # Validate the refined code
                refined_validation = await self.validator.validate(spec, refined_code)
                
                # Create new attempt
                current_attempt = GenerationAttempt(
                    code_files=refined_code,
                    validation=refined_validation,
                    generation_time=current_attempt.generation_time,
                    agent_version=f"{current_attempt.agent_version}_refined_{iteration + 1}"
                )
                
                self._log_debug(f"Refinement {iteration + 1} score: {refined_validation.score:.2f}")
                
            except Exception as e:
                self._log_debug(f"Refinement {iteration + 1} failed: {str(e)}")
                break
        
        return current_attempt
    
    async def _fallback_generation(self, spec: ServiceSpec) -> Tuple[Dict[str, str], ValidationResult]:
        """Fallback to single-agent generation if multi-agent fails"""
        self._log_debug("Falling back to single-agent generation")
        
        try:
            # Simple single-agent generation
            code_files = await self.code_generator.generate_primary(spec)
            
            # Create a basic validation result
            fallback_validation = ValidationResult(
                score=0.7,  # Assume decent quality
                spec_compliance=0.7,
                issues=["Generated with fallback mode"],
                critical_issues=[],
                suggestions=["Consider reviewing generated code"],
                passed=True
            )
            
            return code_files, fallback_validation
            
        except Exception as e:
            # Last resort: return error
            error_files = {"generation_error.txt": f"Multi-agent generation failed: {str(e)}"}
            error_validation = ValidationResult(
                score=0.0, spec_compliance=0.0, issues=["Generation failed"],
                critical_issues=["System error"], suggestions=[], passed=False
            )
            
            return error_files, error_validation


# Main interface class that replaces CodeGenerator
class MultiAgentCodeGenerator:
    """Drop-in replacement for CodeGenerator with multi-agent capabilities"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, debug: bool = False):
        self.orchestrator = MultiAgentOrchestrator(api_key, model, debug)
        self.debug = debug
        
        # For compatibility with existing code
        self.model = self.orchestrator.model
        self.client = self.orchestrator.client
    
    def generate_cloud_function(self, spec: ServiceSpec) -> Dict[str, str]:
        """Main interface - synchronous wrapper for async generation"""
        if self.debug:
            print("🚀 Starting multi-agent code generation...")
        
        try:
            # Run async generation in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            code_files, validation = loop.run_until_complete(
                self.orchestrator.generate_with_validation(spec)
            )
            
            if self.debug:
                print(f"✅ Multi-agent generation completed!")
                print(f"   Validation score: {validation.score:.2f}")
                print(f"   Spec compliance: {validation.spec_compliance:.2f}")
                print(f"   Files generated: {list(code_files.keys())}")
                
                if validation.issues:
                    print(f"   Issues noted: {len(validation.issues)}")
                    for issue in validation.issues[:3]:  # Show first 3
                        print(f"     - {issue}")
            
            return code_files
            
        except Exception as e:
            if self.debug:
                print(f"❌ Multi-agent generation failed: {str(e)}")
            raise
        
        finally:
            loop.close()
    
    async def generate_cloud_function_async(self, spec: ServiceSpec) -> Tuple[Dict[str, str], ValidationResult]:
        """Async interface for advanced usage"""
        return await self.orchestrator.generate_with_validation(spec)


# Convenience function for easy migration
def create_multi_agent_generator(api_key: Optional[str] = None, model: Optional[str] = None, 
                                debug: bool = False) -> MultiAgentCodeGenerator:
    """Factory function to create multi-agent code generator"""
    return MultiAgentCodeGenerator(api_key, model, debug)