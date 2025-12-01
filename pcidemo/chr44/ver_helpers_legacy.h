#pragma once
#include <windows.h>
#include <stdio.h>
#include <string.h>

static FARPROC FindAnyA(HMODULE h, const char** names, int count) {
    int i;
    for (i = 0; i < count; ++i) {
        if (names[i] && names[i][0]) {
            FARPROC p = GetProcAddress(h, names[i]);
            if (p) return p;
        }
    }
    return NULL;
}

static void PrintVerLineA(const char* tagPrefix, const char* kind, const char* v) {
    char tag[64];
#if defined(_MSC_VER)
    _snprintf(tag, sizeof(tag), "%s %s", tagPrefix, kind);
#else
    snprintf(tag, sizeof(tag), "%s %s", tagPrefix, kind);
#endif
    printf("%s: %s\n", tag, (v && v[0]) ? v : "N/A");
}

/*
 * QueryAndPrintDllDriverFW_A:
 *  - dllPathA: e.g. "CHR34XXX.dll" or "Lib\\x64\\CHR34XXX.dll"
 *  - tagPrefix: e.g. "CHR34" or "CHR44"
 *  - devId: board id for FW apis that require it
 *  - dllFns/driverFns/fwFns: arrays of exported function names to try
 *    Preferred signatures tried (in order):
 *      BOOL Fn(char* buf, DWORD bufSize);
 *      BOOL Fn(BYTE devId, char* buf, DWORD bufSize);
 */
static void QueryAndPrintDllDriverFW_A(
    const char* dllPathA,
    const char* tagPrefix,
    BYTE        devId,
    const char** dllFns,   int dllCount,
    const char** driverFns,int driverCount,
    const char** fwFns,    int fwCount
) {
    HMODULE h = LoadLibraryA(dllPathA);
    if (!h) {
        printf("[%s] LoadLibrary failed: %s\n", tagPrefix, dllPathA ? dllPathA : "(null)");
        return;
    }

    typedef BOOL (WINAPI *GET_STR1)(char*, DWORD);
    typedef BOOL (WINAPI *GET_STR2)(BYTE, char*, DWORD);

    {
        char buf[128]; buf[0] = 0;
        GET_STR1 p = (GET_STR1)FindAnyA(h, dllFns, dllCount);
        if (p) {
            if (p(buf, (DWORD)sizeof(buf))) PrintVerLineA(tagPrefix, "dll", buf);
            else                            PrintVerLineA(tagPrefix, "dll", "query failed");
        } else {
            PrintVerLineA(tagPrefix, "dll", "not exported");
        }
    }

    {
        char buf[128]; buf[0] = 0;
        GET_STR1 p = (GET_STR1)FindAnyA(h, driverFns, driverCount);
        if (p) {
            if (p(buf, (DWORD)sizeof(buf))) PrintVerLineA(tagPrefix, "driver", buf);
            else                            PrintVerLineA(tagPrefix, "driver", "query failed");
        } else {
            PrintVerLineA(tagPrefix, "driver", "not exported");
        }
    }

    {
        char buf[128]; buf[0] = 0;
        FARPROC pf = FindAnyA(h, fwFns, fwCount);
        if (pf) {
            BOOL ok = FALSE;
            ok = ((GET_STR1)pf)(buf, (DWORD)sizeof(buf));
            if (!ok) ok = ((GET_STR2)pf)(devId, buf, (DWORD)sizeof(buf));
            if (ok)  PrintVerLineA(tagPrefix, "fw", buf);
            else     PrintVerLineA(tagPrefix, "fw", "query failed");
        } else {
            PrintVerLineA(tagPrefix, "fw", "not exported");
        }
    }

    FreeLibrary(h);
}

