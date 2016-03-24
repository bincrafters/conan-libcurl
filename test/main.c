#include <stdio.h>
#include <curl/curl.h>
#ifndef __APPLE__
#include "openssl/md5.h"
#include "openssl/crypto.h"
#endif
 
int main(void)
{
  CURL *curl;
  CURLcode res;
  int retval = 0;
 
  curl = curl_easy_init();
  if(curl) {
    curl_easy_setopt(curl, CURLOPT_URL, "https://httpbin.org/get");
    res = curl_easy_perform(curl);
 
    if(CURLE_OK == res) {
      char *ct;
      /* ask for the content-type */ 
      res = curl_easy_getinfo(curl, CURLINFO_CONTENT_TYPE, &ct);
 
      if((CURLE_OK == res) && ct) {
        printf("We received Content-Type: %s\n", ct);
      } else {
        printf("No content-type\n");
        retval = 1;
      }
    } else {
      printf("Request failed\n");
      retval = 2;
    }
 
    /* always cleanup */ 
    curl_easy_cleanup(curl);
  } else {
    printf("Failed to init curl\n");
    retval = 3;
  }
  
  return retval;
}
