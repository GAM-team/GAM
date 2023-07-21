
#include "Python.h"
#define _WIN32_WINNT 0x0400	  /* Needed for CryptoAPI on some systems */
#include <windows.h>


static PyObject* getRandomBytes(PyObject *self, PyObject *args)
{
	int howMany;
	HCRYPTPROV hCryptProv;
	unsigned char* bytes = NULL;
	PyObject* returnVal = NULL;


	/* Read Arguments */
    if (!PyArg_ParseTuple(args, "i", &howMany))
    	return(NULL);

	/* Get Context */
	if(CryptAcquireContext(
	   &hCryptProv,
	   NULL,
	   NULL,
	   PROV_RSA_FULL,
	   CRYPT_VERIFYCONTEXT) == 0)
		return Py_BuildValue("s#", NULL, 0);


	/* Allocate bytes */
	bytes = malloc(howMany);


	/* Get random data */
	if(CryptGenRandom(
	   hCryptProv,
	   howMany,
	   bytes) == 0)
		returnVal = Py_BuildValue("s#", NULL, 0);
	else
		returnVal = Py_BuildValue("s#", bytes, howMany);

	free(bytes);
	CryptReleaseContext(hCryptProv, 0);

	return returnVal;
}



/* List of functions exported by this module */

static struct PyMethodDef win32prng_functions[] = {
    {"getRandomBytes", (PyCFunction)getRandomBytes, METH_VARARGS},
    {NULL,  NULL}        /* Sentinel */
};


/* Initialize this module. */

DL_EXPORT(void) initwin32prng(void)
{
    Py_InitModule("win32prng", win32prng_functions);
}
