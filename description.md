# Synopsis
This script should watch a nextcloud directory for changes compare it to the state present in a hugo blog. If a new file or article directory is added, it should create a corresponding merge request to add it to the hugo blog.

# Tech Stack
- Script: Python
- Nextcloud
- GitHub
- Hugo

# Requirements
- The lowest level directory we are interested in for the activity``. The structure is 
    ```
    - Öffentlichkeitsarbeit
        - <year>
            - <activity>
                - <activity_files>
    ```
- Each activity-directory in the nextcloud directory needs to be compared to the existing posts in the hugo blog
- Each activity-directory in the nextcloud directory needs to be compared to the merge requests for the blog
- If a activity-directory is found in the nextcloud directory that is not present in the hugo blog, and no corresponding open merge request is present, a merge request should be created to add it to the hugo blog.
- The merge reqest should be created with the following content:
    - A directory in `content/post/<year>/<ISO-Date>_<activity>`
    - A index.md file with the following content:
        - Frontmatter as described in the technical details below
        - Body as described in the technical details below
    - All media files (.jpg, .png, .JPG, .jpeg, . gif, ...) found in the activity directory. The media files need to be handled with `git lfs` to save space in the repository.

# Techinical details
- The directory structure of the nextcloud directory is as follows:
    ```
    - Öffentlichkeitsarbeit
        - 2022
            - 11.12. Friedenslicht
                - Friedenslicht\ 2022.docx
                - Friedenlicht_2022.jpg
                - kerze.jpg
            - 30.06. Wölflingsversprechen Meute Eichhörnchen
                - Wölflingsversprechen_01.odt
                - DSC07503.JPG
                - PXL_20210814_170200784.jpg
                - ...
            - ...
        - ...
        - 2025
            - 06. - 08.06.2025_Versprechensfeier_Meute Eichhörnchen
                - Versprechensfeier Meute Eichhörnchen.docx
                - IMG_8204.JGP
                - IMG_8238.JPG
                - ...
        - ...
    ```

- The directory structure of the hugo blog is as follows:
    ```
    - content
        - post
            - 2022
                - 2022-12-11_Friedenslicht
                    - index.md
                    - Friedenslicht_2022.jpg
                    - kerze.jpg
                - 2022-09-30_Woelflingsverspechen_meute_eichhörnchen
                    - index.md
                    - verspechen1.jpeg
                    - verspechen2.jpeg
                    - ...
            - 2023
                - ...
            - ...
            - 2025
                2025-06-06_Versprechensfeier_meute_eichhörnchen
                    - index.md
                    - Gruppenfoto.JPG
                    - Gruppenfoto.JPG
                    - ...
    ```

- The index.md of a hugo post starts with a frontmatter like
    ```
    ---
    title: 'Wenzenbacher Pfadfinder bringen als „Lichtträger“ das Friedenslicht aus Bethlehem in die Pfarrgemeinden'
    date: 2022-12-11T02:31:38+02:00
    draft: false
    image: kerze.jpg
    tags: [Friedenslicht]
    description: Wie jedes Jahr bringen wir das Friedenslicht in die Gemeinden
    categories: [Kultur, Stammesleben, Gemeinde]
    ---
    ```

- Below the frontmatter follows the body of the article, e.g.
    ```
    Die Wenzenbacher Pfadfinder brachten in einem festlichen Gottesdienst am 4. Adventssonntag das [Friedenslicht](https://www.friedenslicht.de/) in die Pfarrgemeinde St. Peter.
    Nach dem gemeinsamen Gottesdienst konnte jeder Kirchenbesucher seine mitgebrachte Kerze am Friedenslicht entzünden und mit nach Hause nehmen.

    Dieses Jahr wurde das Friedenslicht nach der Aussendungsfeier im Dom zu Regensburg nach Wenzenbach, Furth im Wald, Sattelpeilnstein und Neutraubling durch die Pfadfinder als „Lichtträger“ weitergereicht.

    > "Mit dem Entzünden und Weitergeben des Friedenslichtes erinnern wir uns an die weihnachtliche Botschaft und an unseren Auftrag, den Frieden unter den Menschen zu verwirklichen."
    > 
    > (www.Friedenslicht.de)

    ![](kerze.jpg) ![](Friedenslichtübergabe.jpg)

    ## Frieden beginnt mit Dir
    Frieden – im Großen wie im Kleinen – kann nur gelingen, wenn alle Menschen mitmachen und sich daran beteiligen. Vor dem Schritt der Beteiligung steht die Frage nach den eigenen Möglichkeiten, Ressourcen und Fähigkeiten oder einfach die Fragen: 
    - Wer bin ich? 
    - Was möchte ich einbringen? 
    - Wie sieht es in mir aus?
    [...]
    ```

