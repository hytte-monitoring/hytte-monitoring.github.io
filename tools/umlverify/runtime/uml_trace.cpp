// The trace runtime of the sequence-diagram flow.
//
// The verifier compiles this file once (without instrumentation) and links it into every
// executable of a project's traced build, whose sources are compiled with
// -finstrument-functions. When the environment variable UML_TRACE_FILE names a file, every
// function entry and exit is appended to it as "E <address>" or "X <address>". The first line,
// "R <address>", is the address of uml_trace_reference(), which lets the verifier undo
// address-space randomisation by comparing it with the executable's symbol table.
//
// No names are resolved here and nothing else happens, so the runtime cannot disturb the
// program it observes. Without UML_TRACE_FILE it does nothing at all.
#include <cstdio>
#include <cstdlib>

extern "C" {

__attribute__((no_instrument_function)) void uml_trace_reference() {}

static FILE* uml_trace_out = nullptr;
static bool uml_trace_tried = false;

__attribute__((no_instrument_function)) static void uml_trace_close()
{
    if (uml_trace_out != nullptr)
    {
        fclose(uml_trace_out);
        uml_trace_out = nullptr;
    }
}

__attribute__((no_instrument_function)) static FILE* uml_trace_file()
{
    if (!uml_trace_tried)
    {
        uml_trace_tried = true;
        const char* path = getenv("UML_TRACE_FILE");
        if (path != nullptr && *path != '\0')
        {
            uml_trace_out = fopen(path, "w");
            if (uml_trace_out != nullptr)
            {
                setvbuf(uml_trace_out, nullptr, _IOLBF, 0);   // survive a crash: one line at a time
                fprintf(uml_trace_out, "R %p\n", reinterpret_cast<void*>(&uml_trace_reference));
                atexit(uml_trace_close);
            }
        }
    }
    return uml_trace_out;
}

__attribute__((no_instrument_function)) void __cyg_profile_func_enter(void* fn, void*)
{
    if (FILE* f = uml_trace_file())
    {
        fprintf(f, "E %p\n", fn);
    }
}

__attribute__((no_instrument_function)) void __cyg_profile_func_exit(void* fn, void*)
{
    if (FILE* f = uml_trace_file())
    {
        fprintf(f, "X %p\n", fn);
    }
}

}  // extern "C"
