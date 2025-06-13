from fastapi import FastAPI, Form, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn
import os
import shutil # For cleaning up temp files
import uuid   # For unique filenames
import subprocess
import traceback # For detailed error logging

# Imports from other project files
from bass import ChordProgression
from drums import DrumPattern
from music21 import stream, note as m21_note, instrument, environment

app = FastAPI()

# Setup Constants and Directories
msc_path = environment.get("musicxmlPath")
if not msc_path:
    print("Warning: MuseScore path not found in music21 environment. WAV generation will fail.")

TEMP_BASE_DIR = "temp_audio_FastAPI"
os.makedirs(TEMP_BASE_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    # from file form.html
    with open("form.html", "r") as file:
        return file.read()

@app.post("/generate_jazz_composition/")
async def generate_composition_endpoint(request: Request, chord_progression: str = Form(...)):
    session_id = str(uuid.uuid4())
    session_temp_dir = os.path.join(TEMP_BASE_DIR, session_id)
    os.makedirs(session_temp_dir, exist_ok=True)

    bass_xml_path = os.path.join(session_temp_dir, "bass_line.xml")
    bass_wav_path = os.path.join(session_temp_dir, "bass_line.wav")
    final_wav_path = os.path.join(session_temp_dir, "final_composition.wav")

    try:
        if not msc_path:
            print("Error: MuseScore path not configured at the time of request.")
            return HTMLResponse("Error: MuseScore path not configured. Cannot generate WAV files.", status_code=500)

        # 1. Parse Chord Progression
        print(f"Session {session_id}: Parsing chord progression:\n{chord_progression}")
        prog = ChordProgression.from_string(chord_progression)

        # 2. Generate Bass Line
        print(f"Session {session_id}: Generating bass line...")
        bassline_notes = prog.generate_bass_line()
        bass_stream = stream.Stream()
        bass_stream.insert(0, instrument.AcousticBass())
        for note_obj in bassline_notes:
            m21_note_obj = m21_note.Note(note_obj.to_midi())
            m21_note_obj.duration.quarterLength = note_obj.length/2
            bass_stream.append(m21_note_obj)

        if len(bass_stream) > 0:
            print(f"Session {session_id}: Writing bass XML to {bass_xml_path}")
            bass_stream.write('musicxml', fp=bass_xml_path)
            print(f"Session {session_id}: Converting bass XML to WAV at {bass_wav_path} using {msc_path}")
            subprocess.run([msc_path, bass_xml_path, '-o', bass_wav_path], check=True, capture_output=True)
            print(f"Session {session_id}: Bass WAV generated.")
        else:
            print(f"Session {session_id}: Bass stream empty or invalid, skipping WAV generation for bass.")



        # 4. Generate Drums and Combine
        print(f"Session {session_id}: Generating drums and combining audio...")
        expanded_prog_items = list(prog)
        total_quarters = sum(item.duration for item in expanded_prog_items if item.is_chord and hasattr(item, 'duration'))

        num_bars = (int(total_quarters) + 3) // 4 # Assuming 4/4 time
        if num_bars == 0 and total_quarters > 0 : num_bars = 1
        if num_bars == 0:
            print(f"Session {session_id}: No calculable bars from progression, defaulting to 4 bars for drums.")
            num_bars = 4

        print(f"Session {session_id}: Calculated {total_quarters} total quarters, resulting in {num_bars} bars for drums.")

        tempo = 120
        num_quarters_per_bar = 4

        drum_machine = DrumPattern(tempo=tempo, num_quarters=num_quarters_per_bar)
        drum_machine.create_pattern(bars=num_bars)
        print(f"Session {session_id}: Drum pattern created with {len(drum_machine.combiner.main_audio)} sound ms.")

        if os.path.exists(bass_wav_path):
            print(f"Session {session_id}: Adding bass WAV to drum combiner.")
            drum_machine.combiner.place_at(bass_wav_path, 0, 0, volume_step=10.0)
        else:
            print(f"Session {session_id}: Bass WAV not found at {bass_wav_path}, not adding to mix.")

        print(f"Session {session_id}: Exporting final combined audio to {final_wav_path}")
        drum_machine.combiner.export(final_wav_path)
        print(f"Session {session_id}: Final WAV exported.")

        # 5. Return FileResponse and schedule cleanup
        background_tasks_for_cleanup = BackgroundTasks()
        background_tasks_for_cleanup.add_task(shutil.rmtree, path=session_temp_dir)
        print(f"Session {session_id}: Scheduled cleanup of {session_temp_dir}")

        return FileResponse(final_wav_path,
                            media_type='audio/wav',
                            filename='jazz_composition.wav',
                            background=background_tasks_for_cleanup)

    except FileNotFoundError as e:
        if msc_path and str(e.filename) == msc_path:
            print(f"Session {session_id}: MuseScore executable not found at: {msc_path}. Error: {e}")
            # Clean up before returning, as FileResponse background task won't run. This is important.
            if os.path.exists(session_temp_dir): shutil.rmtree(session_temp_dir)
            return HTMLResponse(f"Error: MuseScore executable not found at '{msc_path}'. Please configure it correctly.", status_code=500)
        print(f"Session {session_id}: FileNotFoundError in generation: {e}")
        traceback.print_exc()
        # Clean up before returning.
        if os.path.exists(session_temp_dir): shutil.rmtree(session_temp_dir)
        return HTMLResponse(f"Error during generation: File not found - {e.filename}", status_code=500)
    except subprocess.CalledProcessError as e:
        print(f"Session {session_id}: Error during MuseScore conversion. Return code: {e.returncode}")
        print(f"Stdout: {e.stdout.decode() if e.stdout else 'N/A'}")
        print(f"Stderr: {e.stderr.decode() if e.stderr else 'N/A'}")
        traceback.print_exc()
        # Clean up before returning.
        if os.path.exists(session_temp_dir): shutil.rmtree(session_temp_dir)
        return HTMLResponse(f"Error during audio conversion (MuseScore): {e.cmd} failed. Stderr: {e.stderr.decode() if e.stderr else 'N/A'}", status_code=500)
    except Exception as e:
        print(f"Session {session_id}: An unexpected error occurred: {e}")
        traceback.print_exc()
        # Clean up before returning.
        if os.path.exists(session_temp_dir): shutil.rmtree(session_temp_dir)
        return HTMLResponse(f"An unexpected error occurred during generation: {str(e)}", status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
