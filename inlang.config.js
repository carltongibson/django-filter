// init the inlang.config

/**
 * @type {import("@inlang/core/config").DefineConfig}
 */
export async function defineConfig(env) {
  // importing plugin from local file for testing purposes
  const plugin = await env.$import(
    "https://cdn.jsdelivr.net/gh/jannesblobel/inlang-plugin-po@1/dist/index.js"
  );
  const pluginConfig = {
    // language mean the name of you file
    pathPattern: "./django_filters/locale/{language}/LC_MESSAGES/django.po",
    //definte the referenacePath. If you haven't one enter "null"
    referenceResourcePath: null,
  };

  return {
    // if your project use a pot file use the pot as the reference Language
    // !! do not add the pot file in the Languages array
    /**
   * @example
   * example files: en.pot, de.po, es.po, fr.po
   *  referenceLanguage: "en",
      languages: ["de","es","fr"],
   */
    referenceLanguage: "en",
    languages: await getLanguages(env),
    // languages: await getLanguages(env),

    readResources: (args) =>
      plugin.readResources({ ...args, ...env, pluginConfig }),
    writeResources: (args) =>
      plugin.writeResources({ ...args, ...env, pluginConfig }),
  };
}

// /**
//  * Automatically derives the languages in this repository.
//  */
async function getLanguages(env) {
  // languagePath is the place where the languages are stored
  // @example translationsStoredIn = "./translations/" don't forget the / at the end of a path
  const translationsStoredIn = "./django_filters/locale/";
  //get all folders / files which are stored in the translationsStoredIn
  const files = await env.$fs.readdir(translationsStoredIn);
  // files that end with .po
  // remove the .po extension to only get language name
  const languages = [];
  // filter all folder by po files
  for (const language of files) {
    //try to read a po file
    try {
      const file = await env.$fs.readdir(
        translationsStoredIn + language + "/LC_MESSAGES/"
      );
      // somtime are more than 1 file in the folder example: messages.mo and messages.po
      for (const _file of file) {
        if (_file.endsWith(".po")) {
          //if the po file is recognised, the language code is entered into the array languages returned by the function getLangauges
          languages.push(language);
        }
      }
    } catch (error) {}
  }
  return languages;
}
