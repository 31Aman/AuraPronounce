import numpy as np
from typing import List, Dict, Any, Tuple


class ScoringEngine:
    @staticmethod
    def calculate_scores(
        words_data: List[Dict[str, Any]],
        audio_duration: float,
        reference_text: str = None
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Compute pronunciation, fluency, accuracy, completeness, stress, rhythm, and pauses scores.
        Returns a dictionary of scores and an enriched list of words with individual scores."""
        if not words_data:
            return {
                "overall_score": 0.0,
                "fluency_score": 0.0,
                "accuracy_score": 0.0,
                "completeness_score": 0.0,
                "confidence_score": 0.0,
                "stress_score": 0.0,
                "rhythm_score": 0.0,
                "pauses_score": 0.0,
                "timing_score": 0.0,
                "intonation_score": 0.0,
                "phoneme_similarity_score": 0.0
            }, []

        # 1. Individual word scoring and alignment detection
        enriched_words = []
        accuracy_sum = 0.0
        confidence_sum = 0.0
        
        for w in words_data:
            prob = w.get("probability", 0.9)
            # Word accuracy score is based on transcription confidence (0 to 100)
            word_acc = float(prob * 100)
            
            # Identify mispronounced or unclear words based on confidence thresholds
            is_mispronounced = word_acc < 65.0
            is_unclear = 65.0 <= word_acc < 80.0
            
            enriched_words.append({
                "word": w["word"],
                "start_time": w["start"],
                "end_time": w["end"],
                "score": word_acc,
                "is_mispronounced": is_mispronounced,
                "is_unclear": is_unclear,
                # These will be populated by AI G2P alignment if needed
                "phonemes_expected": None,
                "phonemes_actual": None
            })
            accuracy_sum += word_acc
            confidence_sum += word_acc

        mean_accuracy = accuracy_sum / len(words_data)
        mean_confidence = confidence_sum / len(words_data)

        # 2. Pauses & Fluency Calculation
        # We look at the gap between words
        pauses_count = 0
        total_pause_duration = 0.0
        word_durations = []
        
        for i in range(len(words_data)):
            # Word duration
            w_dur = words_data[i]["end"] - words_data[i]["start"]
            word_durations.append(w_dur)
            
            if i < len(words_data) - 1:
                gap = words_data[i+1]["start"] - words_data[i]["end"]
                if gap > 0.5:  # Pause threshold = 500ms
                    pauses_count += 1
                    total_pause_duration += gap

        # Pauses Score: Less unnecessary pauses = higher score
        # A good speaker has about 1-3 natural pauses per 30 seconds.
        # If pauses > 8, the score drops
        pauses_score = max(0.0, 100.0 - (max(0, pauses_count - 3) * 8.0))

        # Speaking Rate (Words Per Minute)
        # Optimal speaking rate is 110-150 WPM.
        speaking_duration = audio_duration - total_pause_duration
        wpm = (len(words_data) / audio_duration) * 60.0
        
        if 110.0 <= wpm <= 150.0:
            speaking_rate_score = 100.0
        elif wpm < 110.0:
            # Too slow
            speaking_rate_score = max(0.0, 100.0 - (110.0 - wpm) * 1.5)
        else:
            # Too fast
            speaking_rate_score = max(0.0, 100.0 - (wpm - 150.0) * 1.2)

        # Fluency Score is a combination of pauses score and speaking rate
        fluency_score = (pauses_score * 0.5) + (speaking_rate_score * 0.5)

        # 3. Completeness Calculation
        if reference_text:
            ref_words = [w.lower().strip(",.?!:;") for w in reference_text.split()]
            ref_words = [w for w in ref_words if w]
            
            # Simple word coverage check
            spoken_set = {w["word"].lower().strip(",.?!:;") for w in words_data}
            matched_count = sum(1 for w in ref_words if w in spoken_set)
            
            completeness_score = (matched_count / len(ref_words)) * 100.0 if ref_words else 100.0
        else:
            # If no reference, assess completeness by whether the audio has regular speech
            speaking_ratio = speaking_duration / audio_duration if audio_duration > 0 else 0.0
            if 0.5 <= speaking_ratio <= 0.85:
                completeness_score = 100.0
            else:
                completeness_score = max(0.0, 100.0 - abs(0.7 - speaking_ratio) * 100.0)

        # 4. Stress, Rhythm, and Timing
        # Rhythm Score: standard deviation of word durations.
        # Native English speakers have high rhythm variability (stress-timing).
        # A standard deviation of word duration around 0.15s to 0.25s is ideal.
        # If it's too flat (stdev < 0.05), it is robotic.
        # If it's too high (stdev > 0.4s), it is hesitant/disjointed.
        dur_std = np.std(word_durations) if word_durations else 0.0
        
        if 0.12 <= dur_std <= 0.28:
            rhythm_score = 95.0
        elif dur_std < 0.12:
            rhythm_score = max(0.0, (dur_std / 0.12) * 95.0)
        else:
            rhythm_score = max(0.0, 95.0 - (dur_std - 0.28) * 150.0)

        # Stress Score: vowel and phoneme duration peaks
        # Let's model stress based on peak duration of long words vs short words
        long_words = [d for w, d in zip(words_data, word_durations) if len(w["word"]) > 6]
        short_words = [d for w, d in zip(words_data, word_durations) if len(w["word"]) <= 3]
        if long_words and short_words:
            ratio = np.mean(long_words) / (np.mean(short_words) + 1e-6)
            # Long words should be ~1.8 to 2.5 times longer than short words in natural speech
            if 1.6 <= ratio <= 2.8:
                stress_score = 98.0
            else:
                stress_score = max(0.0, 98.0 - abs(2.2 - ratio) * 25.0)
        else:
            stress_score = 80.0

        # Timing Score: based on average syllable rate per second
        # Normal speech is 3-5 syllables per second. Let's estimate 1.3 syllables per word.
        syllables_per_second = (len(words_data) * 1.3) / speaking_duration if speaking_duration > 0 else 0
        if 3.0 <= syllables_per_second <= 5.5:
            timing_score = 100.0
        else:
            timing_score = max(0.0, 100.0 - abs(4.25 - syllables_per_second) * 20.0)

        # Intonation and Phoneme Similarity Fallbacks
        intonation_score = max(0.0, mean_accuracy - 2.0)  # estimate
        phoneme_similarity_score = mean_accuracy

        # 5. Overall Weighted Score
        # Overall = 40% Accuracy, 30% Fluency, 20% Completeness, 10% Confidence
        overall_score = (
            (mean_accuracy * 0.40) +
            (fluency_score * 0.30) +
            (completeness_score * 0.20) +
            (mean_confidence * 0.10)
        )

        scores_breakdown = {
            "overall_score": float(np.round(overall_score, 1)),
            "fluency_score": float(np.round(fluency_score, 1)),
            "accuracy_score": float(np.round(mean_accuracy, 1)),
            "completeness_score": float(np.round(completeness_score, 1)),
            "confidence_score": float(np.round(mean_confidence, 1)),
            "stress_score": float(np.round(stress_score, 1)),
            "rhythm_score": float(np.round(rhythm_score, 1)),
            "pauses_score": float(np.round(pauses_score, 1)),
            "timing_score": float(np.round(timing_score, 1)),
            "intonation_score": float(np.round(intonation_score, 1)),
            "phoneme_similarity_score": float(np.round(phoneme_similarity_score, 1))
        }

        return scores_breakdown, enriched_words
